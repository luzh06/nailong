// 拍照模块：取景 → 快门 → 离屏截图 → 存储 → 相册 → 回忆卡。
// 设计依据：此间_剧情与整合方案_v0.2.md 模块 5、此间_相机.md。用法见 projects/cijian-app/README.md。
//
// 照片和屏幕颜色一致的关键：拍照用的是游戏自己的画面管线（pipeline），
// 先画出“玩家看到的那张图”，再在上面叠相机风格。
//
// 宿主要做的事：
//   1. 每帧：if (!photo.render()) pipeline.render(scene, camera)
//   2. photo.active 为 true 时暂停人物移动（视角转动可以保留）
//   3. 需要提示物体（交互点标记等）在照片里消失时，给它 userData.hideInPhoto = true
import * as THREE from 'three';
import { CAMERA_STYLES, FOCAL_LENGTHS, verticalFovForFocal } from './styles.js';
import { GradePass } from './grade.js';
import { StandardPipeline } from '../render/pipeline.js';
import { PhotoStore, ALBUM_LIMIT } from './store.js';
import { Album } from './album.js';
import { playShutter } from './sound.js';

const CROP_HEIGHT = 0.8;   // 取景框高度占屏幕高度的比例
const CROP_WIDTH_MAX = 0.9;
const DEFAULT_KEYS = { toggle: 'KeyC', shoot: 'Space', album: 'KeyB', exit: 'Escape' };

export class PhotoSystem extends EventTarget {
  /**
   * @param {object} o
   * @param {THREE.WebGLRenderer} o.renderer
   * @param {THREE.Scene} o.scene
   * @param {THREE.PerspectiveCamera} o.camera
   * @param {{render: Function, releaseOffscreen?: Function}} [o.pipeline] 游戏的画面管线；不给就用 StandardPipeline
   * @param {HTMLElement} [o.container]   放取景框和相册界面的容器
   * @param {() => object} [o.getContext] 拍照时的情境：{ sceneId, spotId, phase, weather }
   * @param {boolean} [o.bindKeys]        是否由模块自己处理按键和鼠标（C 取景、空格/单击快门、滚轮焦段、B 相册、右键取景）
   * @param {object} [o.keys]             改按键：{ toggle, shoot, album, exit }，值是 KeyboardEvent.code
   * @param {number} [o.captureLongSide]  照片长边像素，默认 3000
   * @param {Array}  [o.spots]            打卡点：[{ id, target: Object3D 或 Vector3, minCoverage?: 0.02, radius?: 0 }]，见 checkSpot()
   */
  constructor({
    renderer,
    scene,
    camera,
    pipeline = null,
    container = document.body,
    getContext = () => ({}),
    bindKeys = true,
    keys = {},
    styleId = 'instant',
    captureLongSide = 3000,
    spots = [],
  }) {
    super();
    this.keys = { ...DEFAULT_KEYS, ...keys };
    this.captureLongSide = captureLongSide;
    this.spots = spots;
    injectCss();
    this.renderer = renderer;
    this.pipeline = pipeline ?? new StandardPipeline(renderer);
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
    this._onResize = () => this.relayout();
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

  /** 宿主窗口大小变了、或宿主改了 camera.fov 之后调用，让取景框和视角重新对上 */
  relayout() {
    this._layout();
  }

  /**
   * 取景时视角被放大了，宿主转视角的鼠标灵敏度乘这个数，长焦时才不会一动就晃过头。
   * 不在取景时是 1。
   */
  get lookScale() {
    if (!this.active) return 1;
    const t = (deg) => Math.tan(THREE.MathUtils.degToRad(deg) / 2);
    return t(this.camera.fov) / t(this._saved.fov);
  }

  /** 拍照实际用的相机（和取景框里看到的一致） */
  captureCamera() {
    const cam = this.camera.clone();
    cam.fov = verticalFovForFocal(this.focalMm, this.style.aspect);
    cam.aspect = this.style.aspect;
    cam.updateProjectionMatrix();
    cam.updateMatrixWorld();
    return cam;
  }

  /**
   * 判断某个打卡点是否被拍进照片：在画面里、没被挡住、占画面够大。
   * @param {{target: THREE.Object3D|THREE.Vector3, minCoverage?: number, radius?: number}} spot
   *   target 是物体时按它的包围盒算；是点时按 radius（米）当作一个球算占比
   * @returns {{ok: boolean, inFrame: boolean, occluded: boolean, coverage: number}}
   */
  checkSpot(spot, cam = this.captureCamera()) {
    const box = new THREE.Box3();
    let center;
    if (spot.target.isObject3D) {
      box.setFromObject(spot.target);
      center = box.getCenter(new THREE.Vector3());
    } else {
      center = spot.target.clone();
      const r = spot.radius ?? 1;
      box.setFromCenterAndSize(center, new THREE.Vector3(r * 2, r * 2, r * 2));
    }
    const frustum = new THREE.Frustum().setFromProjectionMatrix(
      new THREE.Matrix4().multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse),
    );
    const inFrame = frustum.containsPoint(center);
    // 占比：包围盒 8 个角投影到画面后的外接矩形面积（裁到画面内）
    let x0 = 1, y0 = 1, x1 = -1, y1 = -1;
    const v = new THREE.Vector3();
    for (let i = 0; i < 8; i++) {
      v.set(i & 1 ? box.max.x : box.min.x, i & 2 ? box.max.y : box.min.y, i & 4 ? box.max.z : box.min.z).project(cam);
      x0 = Math.min(x0, v.x); x1 = Math.max(x1, v.x);
      y0 = Math.min(y0, v.y); y1 = Math.max(y1, v.y);
    }
    const cw = Math.max(0, Math.min(1, x1) - Math.max(-1, x0));
    const ch = Math.max(0, Math.min(1, y1) - Math.max(-1, y0));
    const coverage = inFrame ? (cw * ch) / 4 : 0;
    // 遮挡：从相机向中心打一条射线，先碰到的不是目标本身就算被挡
    let occluded = false;
    if (inFrame) {
      const dir = center.clone().sub(cam.position);
      const dist = dir.length();
      const ray = new THREE.Raycaster(cam.position, dir.normalize(), cam.near, dist * 0.98);
      const hits = ray.intersectObject(this.scene, true).filter((h) => {
        if (!h.object.visible || h.object.userData.hideInPhoto) return false;
        if (spot.target.isObject3D) {
          let o = h.object;
          while (o) {
            if (o === spot.target) return false;
            o = o.parent;
          }
        }
        return true;
      });
      occluded = hits.length > 0;
    }
    const ok = inFrame && !occluded && coverage >= (spot.minCoverage ?? 0.02);
    return { ok, inFrame, occluded, coverage: +coverage.toFixed(4) };
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
    this.previewRT = new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, depthBuffer: false });
    return this.previewRT;
  }

  /** 取景时代替宿主的那一帧渲染，返回 true 表示这一帧已经画完 */
  render() {
    if (!this.active) return false;
    const r = this.renderer;
    const size = r.getDrawingBufferSize(new THREE.Vector2());
    const rt = this._ensurePreviewTarget(size.x, size.y);
    // 先用游戏管线画出玩家平时看到的画面
    this.pipeline.render(this.scene, this.camera, rt, { width: size.x, height: size.y });

    // 整屏先画一遍（框外会被遮暗），再按照片的取样区域把框内重画一遍，
    // 这样暗角和颗粒的位置与拍出来的照片一致。setViewport / setScissor 用 CSS 像素
    const seed = (performance.now() * 0.06) % 1000;
    this.grade.render(r, rt, null, { width: size.x, height: size.y, seed });
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
      // 打卡点判定：情境里没指定 spotId 时，取第一个拍到的打卡点
      const spotHits = this.spots
        .map((sp) => ({ id: sp.id, ...this.checkSpot(sp, this._lastCam) }))
        .filter((h) => h.ok)
        .map((h) => h.id);
      const meta = {
        id: `p_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`,
        createdOrder: ++this.order,
        createdAt: new Date().toISOString(),
        sceneId: ctx.sceneId ?? null,
        spotId: ctx.spotId ?? spotHits[0] ?? null, // 空表示自由拍摄
        spotHits,
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
    const W = aspect >= 1 ? this.captureLongSide : Math.round(this.captureLongSide * aspect);
    const H = Math.round(W / aspect);

    const cam = this.captureCamera();
    this._lastCam = cam;

    const hidden = [];
    this.scene.traverse((o) => {
      if (o.userData.hideInPhoto && o.visible) {
        o.visible = false;
        hidden.push(o);
      }
    });
    if (!r.shadowMap.autoUpdate) r.shadowMap.needsUpdate = true;

    const srcRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, depthBuffer: false });
    const outRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.UnsignedByteType, depthBuffer: false });
    const prevTarget = r.getRenderTarget();
    try {
      this.pipeline.render(this.scene, cam, srcRT, { width: W, height: H });
      this.grade.render(r, srcRT, outRT, { width: W, height: H, seed: Math.random() * 1000 });
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
      srcRT.dispose();
      outRT.dispose();
      this.pipeline.releaseOffscreen?.();
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
      <div class="photo-hint">滚轮 换焦段 · 单击或${keyName(this.keys.shoot)} 按快门 · ${keyName(this.keys.toggle)} 收起相机 · ${keyName(this.keys.album)} 相册</div>
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
    this._onKey = (e) => {
      if (e.target instanceof HTMLInputElement) return;
      const k = this.keys;
      if (e.code === k.toggle) this.toggle();
      else if (e.code === k.shoot && this.active) {
        e.preventDefault();
        this.shoot();
      } else if (e.code === k.album) this.album.toggle();
      else if (e.code === k.exit) {
        if (this.album.isOpen) this.album.close();
        else this.exit();
      }
    };
    window.addEventListener('keydown', this._onKey);
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
    window.removeEventListener('keydown', this._onKey);
    this.album.dispose();
  }
}

function keyName(code) {
  return code === 'Space' ? '空格' : code.replace(/^Key|^Digit/, '');
}

// 样式表跟着模块走：宿主只要 import，不用另外引 CSS
function injectCss() {
  if (document.querySelector('link[data-cijian-photo]')) return;
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = new URL('./photo.css', import.meta.url).href;
  link.dataset.cijianPhoto = '';
  document.head.appendChild(link);
}
