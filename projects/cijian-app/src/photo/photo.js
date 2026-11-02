// 拍照模块：取景 → 快门 → 离屏截图 → 存储 → 相册 → 回忆卡。
// 只依赖宿主的 renderer、scene、camera，可以直接挪进正式游戏程序。
// 设计依据：此间_剧情与整合方案_v0.2.md 模块 5、此间_相机.md。
//
// 宿主要做的事：
//   1. 每帧：if (!photo.render()) renderer.render(scene, camera)
//   2. photo.active 为 true 时暂停人物移动（视角转动可以保留）
//   3. 需要提示物体（交互点标记等）在照片里消失时，给它 userData.hideInPhoto = true
import * as THREE from 'three';
import { CAMERA_STYLES, FOCAL_LENGTHS, verticalFovForFocal } from './styles.js';
import { GradePass } from './grade.js';
import { PhotoStore, ALBUM_LIMIT } from './store.js';
import { Album } from './album.js';
import { playShutter } from './sound.js';

const CAPTURE_LONG_SIDE = 3000;
const CROP_HEIGHT = 0.8;   // 取景框高度占屏幕高度的比例
const CROP_WIDTH_MAX = 0.9;

export class PhotoSystem extends EventTarget {
  /**
   * @param {object} o
   * @param {THREE.WebGLRenderer} o.renderer
   * @param {THREE.Scene} o.scene
   * @param {THREE.PerspectiveCamera} o.camera
   * @param {HTMLElement} [o.container]   放取景框和相册界面的容器
   * @param {() => object} [o.getContext] 拍照时的情境：{ sceneId, spotId, phase, weather }
   * @param {boolean} [o.bindKeys]        是否由模块自己处理按键（C 取景、空格/单击快门、滚轮焦段、B 相册）
   */
  constructor({ renderer, scene, camera, container = document.body, getContext = () => ({}), bindKeys = true, styleId = 'instant' }) {
    super();
    this.renderer = renderer;
    this.scene = scene;
    this.camera = camera;
    this.container = container;
    this.getContext = getContext;
    this.active = false;
    this.busy = false;
    this.focalIndex = 1; // 35mm
    this.grade = new GradePass();
    this.store = new PhotoStore();
    this.order = 0;
    this.store.list().then((rows) => {
      this.order = rows.reduce((m, r) => Math.max(m, r.meta.createdOrder), 0);
    });

    this._buildUi();
    this.album = new Album(this, container);
    this.setStyle(styleId);
    if (bindKeys) this._bindKeys();
    this._onResize = () => this._layout();
    window.addEventListener('resize', this._onResize);
  }

  get style() {
    return CAMERA_STYLES[this.styleId];
  }

  get focalMm() {
    return FOCAL_LENGTHS[this.focalIndex];
  }

  async setStyle(styleId) {
    if (!CAMERA_STYLES[styleId]) throw new Error(`没有这台相机：${styleId}`);
    this.styleId = styleId;
    await this.grade.setStyle(this.style);
    this.ui.root.dataset.finder = this.style.finder;
    this._layout();
    this.dispatchEvent(new CustomEvent('stylechange', { detail: { styleId } }));
  }

  setFocal(index) {
    this.focalIndex = THREE.MathUtils.clamp(index, 0, FOCAL_LENGTHS.length - 1);
    this._layout();
  }

  enter() {
    if (this.active) return;
    this.active = true;
    this._saved = { fov: this.camera.fov, near: this.camera.near, zoom: this.camera.zoom, aspect: this.camera.aspect };
    this.camera.near = Math.min(this.camera.near, 0.05);
    document.querySelectorAll('[data-hud]').forEach((el) => el.classList.add('photo-hud-hidden'));
    this.ui.root.classList.add('on');
    this._layout();
    this.dispatchEvent(new Event('enter'));
  }

  exit() {
    if (!this.active) return;
    this.active = false;
    Object.assign(this.camera, this._saved);
    this.camera.updateProjectionMatrix();
    document.querySelectorAll('[data-hud]').forEach((el) => el.classList.remove('photo-hud-hidden'));
    this.ui.root.classList.remove('on');
    this.dispatchEvent(new Event('exit'));
  }

  toggle() {
    this.active ? this.exit() : this.enter();
  }

  // 取景框在屏幕上的位置（CSS 像素）
  _crop() {
    const el = this.renderer.domElement;
    const W = el.clientWidth;
    const H = el.clientHeight;
    let h = H * CROP_HEIGHT;
    let w = h * this.style.aspect;
    if (w > W * CROP_WIDTH_MAX) {
      w = W * CROP_WIDTH_MAX;
      h = w / this.style.aspect;
    }
    return { x: (W - w) / 2, y: (H - h) / 2, w, h, W, H };
  }

  // 让取景框里正好是所选焦段的视角
  _layout() {
    if (!this.style) return;
    const c = this._crop();
    Object.assign(this.ui.frame.style, { left: `${c.x}px`, top: `${c.y}px`, width: `${c.w}px`, height: `${c.h}px` });
    this.ui.info.textContent = `${this.style.name} · ${this.focalMm}mm`;
    if (!this.active) return;
    const photoV = THREE.MathUtils.degToRad(verticalFovForFocal(this.focalMm, this.style.aspect));
    const k = c.h / c.H;
    this.camera.fov = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(photoV / 2) / k));
    this.camera.aspect = c.W / c.H;
    this.camera.updateProjectionMatrix();
  }

  _ensurePreviewTarget(w, h) {
    if (this.previewRT && this.previewRT.width === w && this.previewRT.height === h) return this.previewRT;
    this.previewRT?.dispose();
    this.previewRT = new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, samples: 4 });
    return this.previewRT;
  }

  /** 取景时代替宿主的 renderer.render，返回 true 表示这一帧已经画完 */
  render() {
    if (!this.active) return false;
    const r = this.renderer;
    const size = r.getDrawingBufferSize(new THREE.Vector2());
    const rt = this._ensurePreviewTarget(size.x, size.y);
    this.grade.syncToneMapping(r);
    r.setRenderTarget(rt);
    r.render(this.scene, this.camera);

    // 整屏先画一遍（框外会被遮暗），再按照片的取样区域把框内重画一遍，
    // 这样暗角和颗粒的位置与拍出来的照片一致
    const seed = (performance.now() * 0.06) % 1000;
    this.grade.render(r, rt, null, { width: size.x, height: size.y, seed });
    // setViewport / setScissor 用 CSS 像素，渲染器自己乘像素比
    const c = this._crop();
    const dpr = size.x / c.W;
    const vy = c.H - c.y - c.h;
    r.setScissorTest(true);
    r.setScissor(c.x, vy, c.w, c.h);
    r.setViewport(c.x, vy, c.w, c.h);
    this.grade.render(r, rt, null, {
      width: c.w * dpr,
      height: c.h * dpr,
      seed,
      uvRect: [c.x / c.W, vy / c.H, c.w / c.W, c.h / c.H],
    });
    r.setScissorTest(false);
    r.setViewport(0, 0, c.W, c.H);
    return true;
  }

  /** 按下快门。返回保存好的照片记录 { id, meta, blob } */
  async shoot() {
    if (!this.active || this.busy) return null;
    this.busy = true;
    playShutter(this.style.shutter);
    this._shutterAnim();
    // 让快门叶片先合上再截图，读回像素的停顿被动画盖住
    await new Promise((res) => setTimeout(res, 90));
    try {
      const canvas = this._capture();
      // 先用缩小图让照片立刻开始显影，完整 JPEG 在后台编码（约 0.5 秒）
      this.album.showDevelop(canvas, this.styleId);
      const blob = await new Promise((res, rej) =>
        canvas.toBlob((b) => (b ? res(b) : rej(new Error('图片编码失败'))), 'image/jpeg', 0.92),
      );
      const ctx = this.getContext() || {};
      const meta = {
        id: `p_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`,
        createdOrder: ++this.order,
        createdAt: new Date().toISOString(),
        sceneId: ctx.sceneId ?? null,
        spotId: ctx.spotId ?? null,          // 空表示自由拍摄
        phase: ctx.phase ?? null,            // 拍摄时的时段、天气，之后不改
        weather: ctx.weather ?? null,
        cameraStyle: this.styleId,
        camera: {
          position: this.camera.position.toArray(),
          quaternion: this.camera.quaternion.toArray(),
          focalMm: this.focalMm,
        },
      };
      const record = { id: meta.id, meta, blob };
      let saved = true;
      try {
        await this.store.put(record);
      } catch {
        saved = false;
      }
      const total = await this.store.count();
      this.dispatchEvent(new CustomEvent('photo', { detail: { record, saved, persistent: this.store.persistent, total, overLimit: total > ALBUM_LIMIT } }));
      return record;
    } catch (err) {
      // 截图失败不拿别的图冒充，告诉玩家原因让他重拍
      this.dispatchEvent(new CustomEvent('error', { detail: { message: `这张没拍成：${err.message}，再试一次吧。` } }));
      return null;
    } finally {
      this.busy = false;
    }
  }

  // 渲染并读回像素，返回画好照片的 canvas（同步，读回的停顿被快门动画盖住）
  _capture() {
    const r = this.renderer;
    const aspect = this.style.aspect;
    const W = aspect >= 1 ? CAPTURE_LONG_SIDE : Math.round(CAPTURE_LONG_SIDE * aspect);
    const H = Math.round(W / aspect);

    const cam = this.camera.clone();
    cam.fov = verticalFovForFocal(this.focalMm, aspect);
    cam.aspect = aspect;
    cam.updateProjectionMatrix();

    const hidden = [];
    this.scene.traverse((o) => {
      if (o.userData.hideInPhoto && o.visible) {
        o.visible = false;
        hidden.push(o);
      }
    });
    if (!r.shadowMap.autoUpdate) r.shadowMap.needsUpdate = true;

    const sceneRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 });
    const outRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.UnsignedByteType });
    const prevTarget = r.getRenderTarget();
    try {
      this.grade.syncToneMapping(r);
      r.setRenderTarget(sceneRT);
      r.render(this.scene, cam);
      this.grade.render(r, sceneRT, outRT, { width: W, height: H, seed: Math.random() * 1000 });
      const px = new Uint8Array(W * H * 4);
      r.readRenderTargetPixels(outRT, 0, 0, W, H, px);

      const canvas = document.createElement('canvas');
      canvas.width = W;
      canvas.height = H;
      const g = canvas.getContext('2d');
      const img = g.createImageData(W, H);
      const row = W * 4;
      for (let y = 0; y < H; y++) {
        img.data.set(px.subarray((H - 1 - y) * row, (H - y) * row), y * row); // WebGL 的行是倒着的
      }
      g.putImageData(img, 0, 0);
      return canvas;
    } finally {
      r.setRenderTarget(prevTarget);
      sceneRT.dispose();
      outRT.dispose();
      hidden.forEach((o) => (o.visible = true));
    }
  }

  _shutterAnim() {
    const s = this.ui.shutter;
    s.classList.remove('fire');
    void s.offsetWidth;
    s.classList.add('fire');
  }

  _buildUi() {
    const root = document.createElement('div');
    root.className = 'photo-ui';
    root.innerHTML = `
      <div class="photo-frame">
        <div class="photo-thirds"></div>
        <div class="photo-corners"><i></i><i></i><i></i><i></i></div>
        <div class="photo-level"></div>
      </div>
      <div class="photo-info"></div>
      <div class="photo-hint">滚轮 换焦段 · 单击或空格 按快门 · C 收起相机 · B 相册</div>
      <div class="photo-shutter"></div>`;
    this.container.appendChild(root);
    this.ui = {
      root,
      frame: root.querySelector('.photo-frame'),
      level: root.querySelector('.photo-level'),
      info: root.querySelector('.photo-info'),
      shutter: root.querySelector('.photo-shutter'),
    };
  }

  // 水平仪：画面倾斜时那条线跟着转
  updateLevel() {
    if (!this.active) return;
    const e = new THREE.Euler().setFromQuaternion(this.camera.quaternion, 'YXZ');
    this.ui.level.style.transform = `translate(-50%,-50%) rotate(${-THREE.MathUtils.radToDeg(e.z)}deg)`;
  }

  _bindKeys() {
    const el = this.renderer.domElement;
    window.addEventListener('keydown', (e) => {
      if (e.target instanceof HTMLInputElement) return;
      if (e.code === 'KeyC') this.toggle();
      else if (e.code === 'Space' && this.active) {
        e.preventDefault();
        this.shoot();
      } else if (e.code === 'KeyB') this.album.toggle();
      else if (e.code === 'Escape') {
        if (this.album.isOpen) this.album.close();
        else this.exit();
      }
    });
    el.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      this.toggle();
    });
    el.addEventListener(
      'wheel',
      (e) => {
        if (!this.active) return;
        e.preventDefault();
        this.setFocal(this.focalIndex + (e.deltaY > 0 ? -1 : 1));
      },
      { passive: false },
    );
    // 单击（没有拖动视角）才算按快门
    let down = null;
    el.addEventListener('pointerdown', (e) => {
      if (e.button === 0) down = [e.clientX, e.clientY];
    });
    el.addEventListener('pointerup', (e) => {
      if (e.button !== 0 || !down || !this.active) return;
      const moved = Math.hypot(e.clientX - down[0], e.clientY - down[1]);
      down = null;
      if (moved < 5) this.shoot();
    });
  }

  dispose() {
    window.removeEventListener('resize', this._onResize);
    this.previewRT?.dispose();
    this.grade.dispose();
    this.ui.root.remove();
    this.album.dispose();
  }
}
