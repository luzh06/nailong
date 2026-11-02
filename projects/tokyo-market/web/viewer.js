// 此间 实时预览: 读取导出的 GLB, 按材质合批, 走动 + 切光线。坐标: Blender (x, y, z) = three (x, z, -y)。
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const loadEl = document.getElementById('load');
const fail = (e) => { loadEl.style.display = 'flex'; loadEl.textContent = '加载失败: ' + e; console.error(e); };
window.addEventListener('error', (e) => fail(e.message));

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.info.autoReset = false;
document.body.prepend(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, 0.1, 2500);

// 三版光线, 数值对照 build_scene.py 的 LOOKS, 实时渲染再手调
const LOOKS = {
  morning: { top: 0x7fa6d8, horizon: 0xdfe6ea, sun: [125, 25], sunColor: 0xffe0b0, sky2: 0xc4d4e8, sunI: 2.8, hemi: 2.1, hemiGround: 0x8f887c, skyline: 0xb8c8e0, exposure: 0.8, fog: 0xc8d4dc,
    glow: 0, lantern: 0, glass: 0, city: 0, lit: 0, citysign: 0, signs: 0, globe: 0, blossom: 0.05, shops: 0, shuttersDown: true },
  sunset: { top: 0x6f7fa8, horizon: 0xe8b090, sun: [248, 7], sunColor: 0xff9a5a, sky2: 0xc0a8b0, sunI: 2.0, hemi: 1.2, hemiGround: 0x6a5a52, skyline: 0xc8b0a0, exposure: 0.85, fog: 0xc09888,
    glow: 1.1, lantern: 0.9, glass: 0.16, city: 0.55, lit: 0.8, citysign: 0.5, signs: 0.08, globe: 0.5, blossom: 0.1, shops: 6, shuttersDown: false },
  dusk: { top: 0x101d3c, horizon: 0x5a6890, sun: [248, 20], sunColor: 0x8096c8, sky2: 0x34456e, sunI: 0.1, hemi: 0.75, hemiGround: 0x20242e, skyline: 0x28365a, exposure: 1.0, fog: 0x2a3350,
    glow: 1.8, lantern: 1.2, glass: 0.25, city: 0.75, lit: 1.5, citysign: 0.9, signs: 0.3, globe: 1.6, blossom: 0.2, shops: 9, shuttersDown: false },
};

const hemi = new THREE.HemisphereLight(0xffffff, 0x444444, 1);
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xffffff, 1);
sun.castShadow = true;
sun.shadow.mapSize.set(4096, 4096);
sun.shadow.bias = -0.0004;
sun.shadow.normalBias = 0.03;
Object.assign(sun.shadow.camera, { left: -60, right: 60, top: 60, bottom: -60, near: 1, far: 500 });
scene.add(sun, sun.target);

// 渐变天空
const skyUniforms = { top: { value: new THREE.Color() }, horizon: { value: new THREE.Color() } };
const sky = new THREE.Mesh(new THREE.SphereGeometry(2200, 24, 12), new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false, uniforms: skyUniforms,
  vertexShader: 'varying vec3 p; void main(){ p = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `uniform vec3 top; uniform vec3 horizon; varying vec3 p;
    void main(){ float h = clamp(normalize(p).y, 0.0, 1.0); gl_FragColor = vec4(mix(horizon, top, pow(h, 0.45)), 1.0);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`,
}));
sky.frustumCulled = false;
scene.add(sky);
scene.fog = new THREE.Fog(0xffffff, 150, 1500);

// 店内灯: 只开离相机最近的几盏
const shopSpots = [];
const shopLights = Array.from({ length: 8 }, () => {
  const l = new THREE.PointLight(0xffc088, 0, 14, 1.6);
  scene.add(l);
  return l;
});

function b64ToBuffer(b64) {
  const s = atob(b64); const u = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i);
  return u.buffer;
}
const loader = new GLTFLoader();
const parse = (b64) => new Promise((res, rej) => loader.parse(b64ToBuffer(b64), '', res, rej));

const emissiveByName = new Map();

function fixMaterial(m) {
  // 不靠 Blender 导出时那一版的自发光, 由光线版本控制
  if (m.name.startsWith('yn_mat_') || m.name.startsWith('wb_')) {
    if (m.emissiveMap) m.emissive.set(0xffffff);
    emissiveByName.set(m.name, m);
  }
  return m;
}

// 把一批 mesh 烘进世界坐标, 按材质合并成一个 mesh, 2000 多次 Draw Call 能降到几十
function mergeByMaterial(meshes, parent, shadows = true) {
  const groups = new Map();
  for (const mesh of meshes) {
    if (!groups.has(mesh.material)) groups.set(mesh.material, []);
    groups.get(mesh.material).push(mesh);
  }
  const out = [];
  for (const [material, list] of groups) {
    const geos = list.map((mesh) => {
      const src = mesh.geometry;
      const g = new THREE.BufferGeometry();
      for (const name of ['position', 'normal', 'uv']) {
        if (src.attributes[name]) g.setAttribute(name, src.attributes[name].clone());
      }
      if (!g.attributes.uv) g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(g.attributes.position.count * 2), 2));
      g.setIndex(src.index ? src.index.clone() : [...Array(g.attributes.position.count).keys()]);
      mesh.updateWorldMatrix(true, false);
      g.applyMatrix4(mesh.matrixWorld);
      return g;
    });
    const merged = mergeGeometries(geos, false);
    geos.forEach((g) => g.dispose());
    const m = new THREE.Mesh(merged, fixMaterial(material));
    m.castShadow = shadows && !material.transparent;
    m.receiveShadow = true;
    parent.add(m);
    out.push(m);
  }
  return out;
}

function meshesOf(root, filter = () => true) {
  const list = [];
  root.traverse((o) => {
    if (!o.isMesh) return;
    // GLTFLoader 把多材质节点拆成子 mesh, 名字在父节点上
    const owner = o.parent && o.parent.isGroup && o.parent !== root && o.parent.parent ? o.parent : o;
    if (filter(owner.name || o.name)) list.push(o);
  });
  return list;
}

const closedNorenGroup = new THREE.Group();
const shuttersGroup = new THREE.Group();
const crowdGroup = new THREE.Group();
scene.add(closedNorenGroup, shuttersGroup, crowdGroup);
let loaded = false;

async function load() {
  const [sceneGltf, crowdGltf, shutterGltf] = await Promise.all([
    parse(window.GLB_SCENE), parse(window.GLB_CROWD), parse(window.GLB_SHUTTERS),
  ]);
  window.GLB_SCENE = window.GLB_CROWD = window.GLB_SHUTTERS = null;
  for (const g of [sceneGltf, crowdGltf, shutterGltf]) g.scene.updateMatrixWorld(true);

  // 早晨关门的店: 卷帘放下, 对应的暖帘要收起
  const closed = new Set();
  shutterGltf.scene.traverse((o) => {
    const hit = /^(s_[we]\d+)_shutter/.exec(o.name);
    if (hit) closed.add(hit[1] + '_noren');
  });
  const isClosedNoren = (name) => closed.has(name.replace(/\.\d+$/, ''));

  sceneGltf.scene.traverse((o) => {
    if (/^s_[we]\d+_body/.test(o.name)) {
      const p = new THREE.Vector3(); o.getWorldPosition(p);
      p.x -= Math.sign(p.x) * 0.4; p.y = 2.5;  // 檐下, 同时照到店内和街面
      shopSpots.push(p);
    }
  });

  const base = meshesOf(sceneGltf.scene, (n) => !isClosedNoren(n));
  const noren = meshesOf(sceneGltf.scene, isClosedNoren);
  mergeByMaterial(base, scene);
  mergeByMaterial(noren, closedNorenGroup);
  mergeByMaterial(meshesOf(shutterGltf.scene), shuttersGroup);
  mergeByMaterial(meshesOf(crowdGltf.scene), crowdGroup);
  loaded = true;
  loadEl.style.display = 'none';
}

let shadowDirty = true;
let currentLook = 'sunset';
function setLook(name) {
  currentLook = name;
  const L = LOOKS[name];
  skyUniforms.top.value.set(L.top); skyUniforms.horizon.value.set(L.horizon);
  scene.fog.color.set(L.fog);
  const [az, el] = L.sun.map(THREE.MathUtils.degToRad);
  // 方位从北顺时针; Blender +Y 是北, 即 three 的 -Z
  sunDir.set(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el));
  sun.color.set(L.sunColor); sun.intensity = L.sunI;
  hemi.color.set(L.sky2); hemi.groundColor.set(L.hemiGround); hemi.intensity = L.hemi;
  renderer.toneMappingExposure = L.exposure;
  const e = (n, v) => { const m = emissiveByName.get(n); if (m) m.emissiveIntensity = v; };
  e('yn_mat_window', L.city * 1.15);
  const sl = emissiveByName.get('yn_mat_skyline');
  if (sl) { sl.color.set(0x000000); sl.emissive.set(L.skyline); sl.emissiveIntensity = 1; sl.fog = false; } e('yn_mat_bulb', L.glow * 8); e('yn_mat_glow', L.glow); e('yn_mat_lantern', L.lantern); e('yn_mat_glass_dark', L.glass);
  e('yn_mat_landmark_lit', L.lit); e('yn_mat_trim', L.lit * 1.1); e('yn_mat_citysigns', L.citysign);
  e('yn_mat_signs', L.signs); e('yn_mat_plaque', L.signs * 0.7); e('yn_mat_globe', L.globe); e('yn_mat_blossom', L.blossom);
  for (const [n, m] of emissiveByName) if (n.startsWith('yn_mat_city_')) m.emissiveIntensity = L.city;
  shadowDirty = true;
  closedNorenGroup.visible = !L.shuttersDown;
  shuttersGroup.visible = L.shuttersDown;
  document.querySelectorAll('[data-look]').forEach((b) => b.classList.toggle('on', b.dataset.look === name));
}
const sunDir = new THREE.Vector3();

// 机位
const HFOV_MAIN = 2 * Math.atan(18 / 127);
let mode = 'walk', yaw = 0, pitch = 0;
const pos = new THREE.Vector3(-0.7, 1.6, -1.0);
function setCam(name) {
  mode = name;
  if (name === 'main') {
    camera.position.set(10.7, 24, 67.4);
    camera.lookAt(-18, -8.8, -231.2);
    camera.near = 1;
    fitMainFov();
  } else {
    camera.fov = 62; camera.near = 0.1;
    camera.position.copy(pos);
    camera.rotation.set(pitch, yaw, 0, 'YXZ');
  }
  camera.updateProjectionMatrix();
  shadowDirty = true;
  document.querySelectorAll('[data-cam]').forEach((b) => b.classList.toggle('on', b.dataset.cam === name));
}
function fitMainFov() {
  // 例图是竖幅 1320:1787, 让纵向视野和它一样
  const refAspect = 1320 / 1787;
  camera.fov = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(HFOV_MAIN / 2) / refAspect));
}

// 走动: 限制在主街和背巷里, 暂时不做店内碰撞
const keys = new Set();
addEventListener('keydown', (e) => keys.add(e.code));
addEventListener('keyup', (e) => keys.delete(e.code));
// 按住左键拖动看四周; 普通浏览器窗口、预览窗格都能用
let dragging = false;
const cv = renderer.domElement;
cv.addEventListener('pointerdown', (e) => { dragging = true; cv.setPointerCapture(e.pointerId); });
cv.addEventListener('pointerup', () => { dragging = false; });
cv.addEventListener('pointercancel', () => { dragging = false; });
cv.addEventListener('pointermove', (e) => {
  if (!dragging || mode !== 'walk') return;
  yaw += e.movementX * 0.003;
  pitch = THREE.MathUtils.clamp(pitch + e.movementY * 0.003, -1.2, 1.2);
});
function clampWalk(p) {
  const y = -p.z;
  p.z = -THREE.MathUtils.clamp(y, -3, 62);
  const ax = Math.abs(p.x);
  if (ax < 6) p.x = THREE.MathUtils.clamp(p.x, -2.3, 2.3);
  else p.x = Math.sign(p.x) * THREE.MathUtils.clamp(ax, 9.8, 11.9);
}

document.querySelectorAll('[data-look]').forEach((b) => b.addEventListener('click', () => setLook(b.dataset.look)));
document.querySelectorAll('[data-cam]').forEach((b) => b.addEventListener('click', () => setCam(b.dataset.cam)));
document.getElementById('crowd').addEventListener('click', (e) => {
  crowdGroup.visible = !crowdGroup.visible;
  e.currentTarget.classList.toggle('on', crowdGroup.visible);
});
addEventListener('resize', () => {
  renderer.setSize(innerWidth, innerHeight);
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
});

const statsEl = document.getElementById('stats');
const clock = new THREE.Clock();
let frames = 0, acc = 0, fps = 0;
const tmp = new THREE.Vector3();
const shadowFocus = new THREE.Vector3(1e6, 0, 0);
sun.shadow.autoUpdate = false;
function tick() {
  requestAnimationFrame(tick);
  const dt = Math.min(clock.getDelta(), 0.1);
  if (!loaded) return;
  if (mode === 'walk') {
    const speed = (keys.has('ShiftLeft') || keys.has('ShiftRight') ? 3.2 : 1.4) * dt;
    const f = (keys.has('KeyW') ? 1 : 0) - (keys.has('KeyS') ? 1 : 0);
    const s = (keys.has('KeyD') ? 1 : 0) - (keys.has('KeyA') ? 1 : 0);
    pos.x += (-Math.sin(yaw) * f + Math.cos(yaw) * s) * speed;
    pos.z += (-Math.cos(yaw) * f - Math.sin(yaw) * s) * speed;
    clampWalk(pos);
    camera.position.copy(pos);
    camera.rotation.set(pitch, yaw, 0, 'YXZ');
  }
  // 阴影范围跟着相机, 场景是静态的, 走远了才重画一次
  const focus = mode === 'main' ? tmp.set(0, 0, -20) : tmp.copy(camera.position).setY(0);
  if (shadowDirty || focus.distanceToSquared(shadowFocus) > 100) {
    shadowFocus.copy(focus);
    sun.target.position.copy(focus);
    sun.position.copy(focus).addScaledVector(sunDir, 250);
    sun.shadow.needsUpdate = true;
    shadowDirty = false;
  }
  sky.position.copy(camera.position);
  // 最近的店内灯
  const power = LOOKS[currentLook].shops;
  const near = shopSpots.slice().sort((a, b) => a.distanceToSquared(camera.position) - b.distanceToSquared(camera.position));
  shopLights.forEach((l, i) => { if (near[i]) { l.position.copy(near[i]); l.intensity = power; } });

  renderer.info.reset();
  renderer.render(scene, camera);
  frames++; acc += dt;
  if (acc >= 0.5) {
    fps = frames / acc; frames = 0; acc = 0;
    statsEl.textContent = `${fps.toFixed(0)} FPS · ${renderer.info.render.calls} Draw Call · ${(renderer.info.render.triangles / 1000).toFixed(0)}k 三角面`;
    window.__stats = { fps, calls: renderer.info.render.calls, tris: renderer.info.render.triangles };
  }
}

const gl = renderer.getContext();
const dbg = gl.getExtension('WEBGL_debug_renderer_info');
window.__viewer = { setPose(x, z, y2, p) { pos.x = x; pos.z = z; yaw = y2; pitch = p; }, gpu: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : 'unknown', setLook, setCam, get pos() { return pos; }, setYaw(v) { yaw = v; }, renderer, get loaded() { return loaded; } };
tick();
load().then(() => { setLook('sunset'); setCam('walk'); }).catch((e) => fail(e.message || e));
