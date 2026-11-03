// 此间 · 东京主场景 · 键鼠/触屏输入模块
//
// 这个模块只产生“输入意图”，不修改相机/玩家坐标，不读取导航，也不做碰撞。
// 宿主每帧调用 getMoveIntent()，再把 forward/right 交给统一碰撞控制器。
//
// 参考（只借鉴架构，没有复制第三方源码）：
// - three.js r170 examples/games_fps.html + PointerLockControls.js (MIT)
//   keyStates 按 event.code 记录；mousemove 只在 pointerLockElement 命中时消费；
//   connect/disconnect 成对增删 document 监听；pointerlockerror 单独处理。
// - NippleJS (MIT)：static 摇杆、pointer identifier、归一化 vector/force、destroy 清理。
// - swift502/Sketchbook (MIT，已归档)：InputManager 集中收取事件后转发给 IInputReceiver；
//   resetControls 清空动作状态；移动方向由角色读取，不在输入层直接改位置。
// - Rapier character controller 文档 (Apache-2.0)：desiredTranslation 与
//   computedMovement 分离；输入应是“想怎么走”，碰撞修正交给 controller。
//
// 注意：目标工程是 Three.js r170，但本文件不 import three，也不依赖任何第三方包。

const MODES = new Set(['view', 'walk', 'blocked']);
const MOVE_CODES = new Set([
  'KeyW', 'KeyA', 'KeyS', 'KeyD',
  'ArrowUp', 'ArrowLeft', 'ArrowDown', 'ArrowRight'
]);
const SHIFT_CODES = new Set(['ShiftLeft', 'ShiftRight']);
const CSS_URL = new URL('./experience-controls.css', import.meta.url).href;

// 每文档一份样式表引用计数；重复创建/销毁不重复插入、也不提前移除别人的样式。
const styleRegistry = new WeakMap();
let instanceSeq = 0;

export function createExperienceControls(options = {}) {
  const {
    canvas,
    container = null,
    onLook = () => {},
    onZoom = () => {},
    onExit = () => {},
    onHint = () => {},
    // 以下为测试/混合设备用的可选参数，不属于固定接口的核心部分。
    touch = undefined,
    pointerLock = 'auto',
    pointerLockTimeout = 1200,
    deadzone = 0.12
  } = options || {};

  if (!canvas || typeof canvas.addEventListener !== 'function') {
    throw new TypeError('createExperienceControls: canvas is required');
  }
  const doc = container?.ownerDocument || canvas.ownerDocument || globalThis.document;
  const win = doc?.defaultView || globalThis.window;
  const host = container || doc?.body;
  if (!doc || !win || !host) {
    throw new TypeError('createExperienceControls: document/container is required');
  }

  const hasTouch = typeof touch === 'boolean' ? touch : detectTouch(win);
  const style = acquireStyle(doc);
  const helpId = `xc-help-${++instanceSeq}`;
  const root = doc.createElement('div');
  root.className = 'xc-root';
  root.dataset.xcRoot = '';
  root.dataset.xcMode = 'view';
  root.dataset.xcTouch = hasTouch ? 'true' : 'false';
  root.setAttribute('role', 'group');
  root.setAttribute('aria-label', '场景操作');

  if (hasTouch) {
    root.innerHTML = `
      <div class="xc-stick" data-xc-stick>
        <div class="xc-stick-base" data-xc-stick-base role="group"
             aria-label="移动摇杆，向上推前进，向右推右移" aria-describedby="${helpId}">
          <div class="xc-stick-knob" data-xc-stick-knob aria-hidden="true"></div>
        </div>
        <span class="xc-stick-label" aria-hidden="true">移动</span>
      </div>
      <p class="xc-touch-help" id="${helpId}" role="note">拖动画面环视 · 进入行走后用左侧摇杆移动</p>
      <button class="xc-exit" type="button" aria-label="退出行走">退出</button>`;
  }
  host.append(root);

  const stickEl = root.querySelector('.xc-stick');
  const baseEl = root.querySelector('.xc-stick-base');
  const knobEl = root.querySelector('.xc-stick-knob');
  const helpEl = root.querySelector('.xc-touch-help');
  const exitEl = root.querySelector('.xc-exit');

  const state = {
    disposed: false,
    mode: 'view',
    keys: new Set(),
    hint: '',
    look: { id: null, x: 0, y: 0 },
    stick: { id: null, forward: 0, right: 0, rect: null },
    lock: {
      active: false,
      pending: false,
      state: 'none',
      expectingUnlock: false,
      timeout: 0,
      guard: 0
    }
  };

  // Canvas 上的触屏手势必须完全由本模块处理；退出时恢复原 inline 值。
  const prevTouchAction = canvas.style ? canvas.style.touchAction : undefined;
  if (canvas.style) canvas.style.touchAction = 'none';

  // ---------------------------------------------------------------- helpers
  const isEditable = (el) => {
    if (!el || el.nodeType !== 1) return false;
    const tag = el.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true;
    if (el.isContentEditable === true) return true;
    return typeof el.closest === 'function' && Boolean(el.closest('[contenteditable="true"]'));
  };

  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

  const capture = (el, id) => {
    try { el?.setPointerCapture?.(id); } catch { /* synthetic pointer in tests */ }
  };
  const releaseCapture = (el, id) => {
    try { el?.releasePointerCapture?.(id); } catch { /* already lost */ }
  };

  const clearLockTimer = () => {
    if (state.lock.timeout) {
      win.clearTimeout(state.lock.timeout);
      state.lock.timeout = 0;
    }
  };
  const clearGuardTimer = () => {
    if (state.lock.guard) {
      win.clearTimeout(state.lock.guard);
      state.lock.guard = 0;
    }
  };

  function endLook() {
    const id = state.look.id;
    state.look.id = null;
    if (id !== null) releaseCapture(canvas, id);
  }

  function resetStick() {
    const id = state.stick.id;
    state.stick.id = null;
    state.stick.forward = 0;
    state.stick.right = 0;
    state.stick.rect = null;
    if (id !== null) releaseCapture(baseEl, id);
    if (stickEl) stickEl.dataset.active = 'false';
    if (knobEl) knobEl.style.transform = 'translate3d(0px, 0px, 0)';
  }

  function clearInput() {
    state.keys.clear();
    endLook();
    resetStick();
  }

  // 宿主回调是模块边界：回调抛错不能把输入循环带崩（world.js 的全局 error
  // 监听会显示致命错误页），但也不能静默吞掉。每个实例只记录一次，避免每帧刷屏。
  let callbackErrorReported = false;
  function invokeCallback(fn, arg, label) {
    try {
      fn(arg);
    } catch (error) {
      if (callbackErrorReported) return;
      callbackErrorReported = true;
      try { console.error(`[experience-controls] ${label} callback failed`, error); } catch { /* ignore */ }
    }
  }

  // ---------------------------------------------------------------- hints
  function hintForMode() {
    if (state.disposed || state.mode === 'blocked') return '';
    if (state.mode === 'view') {
      return hasTouch
        ? '拖动画面环视 · 进入行走后用左侧摇杆移动'
        : '拖动环视 · 滚轮调整视角 · 进入行走后 WASD 移动';
    }
    if (hasTouch) return '左侧摇杆移动 · 右侧拖动环视';
    return state.lock.active
      ? '鼠标环视 · WASD/方向键移动 · Shift 加速 · Esc 退出'
      : 'WASD/方向键移动 · Shift 加速 · 拖动画面环视 · Esc 退出';
  }

  function emitHint(force = false) {
    const text = hintForMode();
    if (!force && text === state.hint) return;
    state.hint = text;
    invokeCallback(onHint, text, 'onHint');
  }

  function updateRoot() {
    root.dataset.xcMode = state.mode;
    if (helpEl) {
      helpEl.textContent = state.mode === 'walk'
        ? '左侧摇杆移动 · 右侧拖动环视'
        : '拖动画面环视 · 进入行走后用左侧摇杆移动';
    }
  }

  // ---------------------------------------------------------------- pointer lock
  function shouldAttemptPointerLock() {
    if (pointerLock === false) return false;
    if (pointerLock === true) return true;
    if (typeof canvas.requestPointerLock !== 'function') return false;
    try {
      const fine = win.matchMedia && win.matchMedia('(pointer: fine)');
      if (fine && fine.matches) return true;
      const coarse = win.matchMedia && win.matchMedia('(pointer: coarse)');
      if (coarse && coarse.matches) return false;
    } catch { /* matchMedia 不可用时按设备触摸能力判断 */ }
    return !hasTouch;
  }

  function requestPointerLock() {
    if (state.disposed) return;
    if (!shouldAttemptPointerLock()) {
      state.lock.state = 'fallback';
      emitHint();
      return;
    }
    // 新的行走请求会取代之前“离开行走”的解锁事件；否则旧 guard 可能
    // 把下一次真正的锁丢失误当成自己触发的解锁而忽略。
    state.lock.expectingUnlock = false;
    clearGuardTimer();
    state.lock.pending = true;
    state.lock.state = 'pending';
    clearLockTimer();
    state.lock.timeout = win.setTimeout(() => {
      state.lock.timeout = 0;
      if (!state.disposed && state.lock.pending && !state.lock.active && state.mode === 'walk') {
        failLock();
      }
    }, Math.max(100, pointerLockTimeout));

    let promise;
    try {
      promise = canvas.requestPointerLock();
    } catch {
      failLock();
      return;
    }
    // Chrome 新版本返回 Promise；旧版本返回 undefined。两种情况都不能留下
    // unhandled rejection，真正的锁状态仍以 pointerlockchange 为准。
    if (promise && typeof promise.then === 'function') {
      Promise.resolve(promise)
        .then(() => {
          // dispose 之后才 resolve 的锁不能把页面留在“无监听器但仍锁定”的状态。
          if (state.disposed && doc.pointerLockElement === canvas) {
            try { doc.exitPointerLock?.(); } catch { /* ignore */ }
          }
        })
        .catch(() => failLock());
    }
    emitHint();
  }

  function failLock() {
    if (state.disposed) return;
    state.lock.pending = false;
    if (state.mode === 'walk' && !state.lock.active) {
      state.lock.state = 'fallback';
      clearLockTimer();
      emitHint();
    }
  }

  function releasePointerLock() {
    clearLockTimer();
    state.lock.pending = false;
    const actuallyLocked = doc.pointerLockElement === canvas;
    state.lock.active = false;
    if (actuallyLocked) {
      state.lock.expectingUnlock = true;
      clearGuardTimer();
      state.lock.guard = win.setTimeout(() => {
        state.lock.guard = 0;
        state.lock.expectingUnlock = false;
      }, 800);
      try { doc.exitPointerLock?.(); } catch { /* ignore */ }
    }
  }

  function onPointerLockChange() {
    if (state.disposed) return;
    const locked = doc.pointerLockElement === canvas;
    if (locked) {
      state.lock.expectingUnlock = false;
      clearGuardTimer();
      state.lock.pending = false;
      state.lock.active = true;
      clearLockTimer();
      if (state.mode !== 'walk') {
        // 例如释放过程中浏览器晚到的 lock 回调；立刻退还，不让它影响 UI 模式。
        releasePointerLock();
        emitHint();
        return;
      }
      endLook();
      emitHint();
      return;
    }

    const wasActive = state.lock.active;
    state.lock.active = false;
    state.lock.pending = false;
    clearLockTimer();
    if (state.lock.expectingUnlock) {
      state.lock.expectingUnlock = false;
      clearGuardTimer();
      emitHint();
      return;
    }
    if (wasActive && state.mode === 'walk') {
      exitWalk('pointerlock-lost');
      return;
    }
    emitHint();
  }

  function onPointerLockError() {
    if (state.lock.pending || state.lock.active) failLock();
  }

  function onMouseMove(event) {
    if (state.disposed || state.mode !== 'walk' || !state.lock.active) return;
    const dx = Number(event.movementX) || 0;
    const dy = Number(event.movementY) || 0;
    if (dx || dy) invokeCallback(onLook, { dx, dy, source: 'lock' }, 'onLook');
  }

  // ---------------------------------------------------------------- keyboard
  function onKeyDown(event) {
    if (state.disposed) return;
    if (event.isComposing) return;
    // 输入框/textarea/select/contenteditable 拥有键盘。按钮（包括旧版“行走”
    // 按钮）不在此列，所以按钮保持焦点时 WASD 仍然有效。
    if (isEditable(doc.activeElement) || isEditable(event.target)) return;

    if (event.code === 'Escape') {
      if (state.mode === 'walk') {
        if (event.cancelable) event.preventDefault();
        exitWalk('escape');
      }
      return;
    }
    if (state.mode !== 'walk') return;
    if (event.ctrlKey || event.metaKey || event.altKey) return;

    if (MOVE_CODES.has(event.code) || SHIFT_CODES.has(event.code)) {
      state.keys.add(event.code);
      if (MOVE_CODES.has(event.code) && event.cancelable) event.preventDefault();
    }
  }

  function onKeyUp(event) {
    if (state.disposed) return;
    // keyup 不检查焦点，避免用户切到输入框后旧按键状态卡住。
    state.keys.delete(event.code);
  }

  function onWindowBlur() {
    if (state.disposed) return;
    clearInput();
  }

  function onVisibilityChange() {
    if (state.disposed) return;
    if (doc.hidden) clearInput();
  }

  function onFocusIn(event) {
    if (state.disposed) return;
    if (isEditable(event.target) || isEditable(doc.activeElement)) clearInput();
  }

  // ---------------------------------------------------------------- pointer look
  function onCanvasPointerDown(event) {
    if (state.disposed || state.mode === 'blocked') return;
    if (event.target !== canvas) return;
    if (state.look.id !== null) return;
    if (event.pointerType === 'mouse' && event.button !== 0) return;

    if (state.mode === 'walk' && state.lock.active) {
      // 鼠标锁定时鼠标由 mousemove 负责；触摸/触控笔则主动退回拖动环视。
      if (event.pointerType === 'touch' || event.pointerType === 'pen') {
        releasePointerLock();
        state.lock.state = 'fallback';
        emitHint();
      } else {
        return;
      }
    }

    state.look.id = event.pointerId;
    state.look.x = event.clientX;
    state.look.y = event.clientY;
    if (event.cancelable) event.preventDefault();
    capture(canvas, event.pointerId);
  }

  function updateLook(event) {
    const dx = event.clientX - state.look.x;
    const dy = event.clientY - state.look.y;
    state.look.x = event.clientX;
    state.look.y = event.clientY;
    if (dx || dy) invokeCallback(onLook, { dx, dy, source: 'drag' }, 'onLook');
  }

  function onPointerMove(event) {
    if (state.disposed || state.mode === 'blocked') return;
    if (state.look.id === event.pointerId) {
      updateLook(event);
      if (event.cancelable) event.preventDefault();
      return;
    }
    if (state.stick.id === event.pointerId) {
      updateStick(event);
      if (event.cancelable) event.preventDefault();
    }
  }

  function onPointerUp(event) {
    if (state.disposed) return;
    if (state.look.id === event.pointerId) endLook();
    if (state.stick.id === event.pointerId) resetStick();
  }

  function onCanvasLostCapture(event) {
    if (state.look.id === event.pointerId) state.look.id = null;
  }

  function onStickLostCapture(event) {
    if (state.stick.id === event.pointerId) resetStick();
  }

  function onWheel(event) {
    if (state.disposed || state.mode === 'blocked') return;
    if (event.ctrlKey || event.metaKey) return;
    if (!event.deltaY) return;
    if (event.cancelable) event.preventDefault();
    invokeCallback(onZoom, { deltaY: event.deltaY, source: 'wheel' }, 'onZoom');
  }

  // ---------------------------------------------------------------- touch stick
  function onStickPointerDown(event) {
    if (state.disposed || state.mode !== 'walk' || !baseEl) return;
    if (state.stick.id !== null) return;
    if (event.pointerType === 'mouse' && event.button !== 0) return;
    if (event.cancelable) event.preventDefault();
    event.stopPropagation();

    // 触摸设备不应被鼠标锁困住：任何触屏操作都退回可拖动环视。
    if (state.lock.active) {
      releasePointerLock();
      state.lock.state = 'fallback';
      emitHint();
    }

    state.stick.id = event.pointerId;
    state.stick.rect = baseEl.getBoundingClientRect();
    stickEl.dataset.active = 'true';
    updateStick(event);
    capture(baseEl, event.pointerId);
  }

  function updateStick(event) {
    if (!baseEl) return;
    const rect = state.stick.rect || baseEl.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const radius = rect.width / 2;
    const knobRect = knobEl ? knobEl.getBoundingClientRect() : null;
    const knobRadius = knobRect ? knobRect.width / 2 : 0;
    const travel = Math.max(1, radius - knobRadius);
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = event.clientX - cx;
    const dy = event.clientY - cy;
    const distance = Math.hypot(dx, dy);
    const limited = Math.min(distance, travel);
    let nx = 0;
    let ny = 0;
    if (distance > 0.0001) {
      nx = dx / distance;
      ny = dy / distance;
    }

    // NippleJS 的 vector/force 语义：单位方向 + 0..1 力度；这里再叠一个死区。
    let force = limited / travel;
    force = force <= deadzone ? 0 : (force - deadzone) / (1 - deadzone);
    force = clamp(force, 0, 1);
    state.stick.right = nx * force;
    state.stick.forward = -ny * force;

    if (knobEl) {
      knobEl.style.transform = `translate3d(${nx * limited}px, ${ny * limited}px, 0)`;
    }
  }

  function onExitClick(event) {
    event.preventDefault();
    event.stopPropagation();
    exitWalk('control-exit');
  }

  // ---------------------------------------------------------------- mode / exit
  function setMode(next) {
    if (state.disposed) return;
    if (!MODES.has(next)) throw new TypeError(`unknown controls mode: ${next}`);
    if (next === state.mode) {
      if (next === 'blocked') {
        clearInput();
        releasePointerLock();
        state.lock.state = 'none';
      }
      updateRoot();
      emitHint();
      return;
    }

    state.mode = next;
    clearInput();

    if (next !== 'walk') {
      releasePointerLock();
      state.lock.state = 'none';
    }
    updateRoot();

    if (next === 'walk') {
      state.lock.state = 'fallback';
      requestPointerLock();
    }
    emitHint();
  }

  function exitWalk(reason) {
    if (state.disposed || state.mode !== 'walk') return;
    state.mode = 'view';
    clearInput();
    updateRoot();
    releasePointerLock();
    state.lock.state = 'none';
    emitHint();
    invokeCallback(onExit, { reason }, 'onExit');
  }

  function getMoveIntent() {
    if (state.disposed || state.mode !== 'walk') {
      return { forward: 0, right: 0, sprint: false };
    }
    let forward = 0;
    let right = 0;
    if (state.keys.has('KeyW') || state.keys.has('ArrowUp')) forward += 1;
    if (state.keys.has('KeyS') || state.keys.has('ArrowDown')) forward -= 1;
    if (state.keys.has('KeyD') || state.keys.has('ArrowRight')) right += 1;
    if (state.keys.has('KeyA') || state.keys.has('ArrowLeft')) right -= 1;
    forward += state.stick.forward;
    right += state.stick.right;
    const length = Math.hypot(forward, right);
    if (length > 1) {
      forward /= length;
      right /= length;
    }
    return {
      forward: clamp(forward, -1, 1),
      right: clamp(right, -1, 1),
      sprint: state.keys.has('ShiftLeft') || state.keys.has('ShiftRight')
    };
  }

  function reset() {
    if (state.disposed) return;
    clearInput();
  }

  function dispose() {
    if (state.disposed) return;
    state.disposed = true;
    clearInput();
    clearLockTimer();
    clearGuardTimer();

    win.removeEventListener('keydown', onKeyDown, { passive: false });
    win.removeEventListener('keyup', onKeyUp);
    win.removeEventListener('blur', onWindowBlur);
    win.removeEventListener('pointermove', onPointerMove, { passive: false });
    win.removeEventListener('pointerup', onPointerUp);
    win.removeEventListener('pointercancel', onPointerUp);
    doc.removeEventListener('visibilitychange', onVisibilityChange);
    doc.removeEventListener('focusin', onFocusIn, true);
    doc.removeEventListener('pointerlockchange', onPointerLockChange);
    doc.removeEventListener('pointerlockerror', onPointerLockError);
    doc.removeEventListener('mousemove', onMouseMove);
    canvas.removeEventListener('pointerdown', onCanvasPointerDown, { passive: false });
    canvas.removeEventListener('wheel', onWheel, { passive: false });
    canvas.removeEventListener('lostpointercapture', onCanvasLostCapture);
    if (baseEl) {
      baseEl.removeEventListener('pointerdown', onStickPointerDown, { passive: false });
      baseEl.removeEventListener('lostpointercapture', onStickLostCapture);
    }
    if (exitEl) exitEl.removeEventListener('click', onExitClick);

    if (doc.pointerLockElement === canvas) {
      try { doc.exitPointerLock?.(); } catch { /* ignore */ }
    }
    state.lock.active = false;
    state.lock.pending = false;
    state.lock.expectingUnlock = false;

    if (canvas.style) canvas.style.touchAction = prevTouchAction === undefined ? '' : prevTouchAction;
    root.remove();
    releaseStyle(doc, style);
  }

  // ---------------------------------------------------------------- listeners
  win.addEventListener('keydown', onKeyDown, { passive: false });
  win.addEventListener('keyup', onKeyUp);
  win.addEventListener('blur', onWindowBlur);
  // 指针移动/抬起放在 window：即使 pointer capture 在合成事件里不可用，
  // 也能保证两个 pointerId（摇杆/环视）彼此独立且松手即停。
  win.addEventListener('pointermove', onPointerMove, { passive: false });
  win.addEventListener('pointerup', onPointerUp);
  win.addEventListener('pointercancel', onPointerUp);
  doc.addEventListener('visibilitychange', onVisibilityChange);
  doc.addEventListener('focusin', onFocusIn, true);
  doc.addEventListener('pointerlockchange', onPointerLockChange);
  doc.addEventListener('pointerlockerror', onPointerLockError);
  doc.addEventListener('mousemove', onMouseMove);
  canvas.addEventListener('pointerdown', onCanvasPointerDown, { passive: false });
  canvas.addEventListener('wheel', onWheel, { passive: false });
  canvas.addEventListener('lostpointercapture', onCanvasLostCapture);
  if (baseEl) {
    baseEl.addEventListener('pointerdown', onStickPointerDown, { passive: false });
    baseEl.addEventListener('lostpointercapture', onStickLostCapture);
  }
  if (exitEl) exitEl.addEventListener('click', onExitClick);

  updateRoot();
  emitHint(true);

  return {
    setMode,
    getMoveIntent,
    reset,
    dispose
  };
}

// ---------------------------------------------------------------- utilities
function detectTouch(win) {
  try {
    if (win.matchMedia) {
      const coarse = win.matchMedia('(pointer: coarse)');
      if (coarse && coarse.matches) return true;
      const fine = win.matchMedia('(pointer: fine)');
      if (fine && fine.matches) return false;
    }
  } catch { /* ignore */ }
  try {
    return (win.navigator?.maxTouchPoints || 0) > 0;
  } catch {
    return false;
  }
}

function acquireStyle(doc) {
  const existing = styleRegistry.get(doc);
  if (existing) {
    existing.count += 1;
    return existing;
  }
  let link = doc.querySelector('link[data-xc-style]');
  let created = false;
  if (!link) {
    link = Array.from(doc.querySelectorAll('link[rel="stylesheet"]'))
      .find((candidate) => candidate.href === CSS_URL) || null;
  }
  if (!link) {
    link = doc.createElement('link');
    link.rel = 'stylesheet';
    link.href = CSS_URL;
    link.dataset.xcStyle = '';
    (doc.head || doc.documentElement).append(link);
    created = true;
  }
  const record = { link, created, count: 1 };
  styleRegistry.set(doc, record);
  return record;
}

function releaseStyle(doc, record) {
  const current = styleRegistry.get(doc);
  if (!current || current !== record) return;
  current.count -= 1;
  if (current.count > 0) return;
  styleRegistry.delete(doc);
  if (current.created && current.link?.isConnected) current.link.remove();
}
