// 拍照模块的独立测试页：用占位几何摆出东京、悉尼的打卡点，代替还没接进来的正式场景。
// 正式接入时照着这里的调用做：建管线 → new PhotoSystem({...城市配置}) → setupCity() → 每帧 render。
//
//   ?city=tokyo（默认）  东京：烘焙小样同款管线（HDR → 泛光 → 曝光 → AgX 查找表），查找表读 test-data/
//   ?city=sydney         悉尼：EffectComposer（泛光 + ACES），和 sydney-harbour 一样
//   ?pipeline=standard | composer | hdr  强制换管线
import * as THREE from 'three';
import { PhotoSystem, HdrPipeline, StandardPipeline, ComposerPipeline } from './photo/index.js';
import { CITIES, setupCity, applyPhase, createTokyoPipeline, createSydneyPipeline, stampFor } from './photo/presets/index.js';
import { buildTokyo } from './test-scenes/tokyo.js';
import { buildSydney } from './test-scenes/sydney.js';

const params = new URLSearchParams(location.search);
const cityId = CITIES[params.get('city')] ? params.get('city') : 'tokyo';
const CITY = CITIES[cityId];

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.prepend(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, 0.1, 400);
const hemi = new THREE.HemisphereLight(0xbcd3ff, 0x6b5a48, 1.2);
const sun = new THREE.DirectionalLight(0xffffff, 3);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.bias = -0.0004;
sun.shadow.normalBias = 0.02;
scene.add(hemi, sun, sun.target);

const world = (cityId === 'sydney' ? buildSydney : buildTokyo)({ renderer, scene, sun, hemi });
camera.far = world.far;
camera.updateProjectionMatrix();

// ---- 画面管线 ----
async function makePipeline() {
  const want = params.get('pipeline') ?? (cityId === 'sydney' ? 'composer' : 'hdr');
  if (want === 'composer') {
    const p = await createSydneyPipeline(renderer, scene, camera);
    addEventListener('resize', () => p.composer.setSize(innerWidth, innerHeight));
    return p;
  }
  if (want === 'hdr') {
    try {
      return await createTokyoPipeline(renderer, { lutBase: 'test-data/' });
    } catch (e) {
      console.warn('读不到查找表，改用 StandardPipeline', e);
    }
  }
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  return new StandardPipeline(renderer);
}
const pipeline = await makePipeline();
document.getElementById('pipe-info').textContent =
  pipeline instanceof HdrPipeline
    ? '东京烘焙小样同款（泛光 + AgX）'
    : pipeline instanceof ComposerPipeline
      ? '悉尼同款（EffectComposer 泛光 + ACES）'
      : 'Three.js ACES';

// ---- 拍照模块：城市配置直接展开，再一步接好打卡点和回忆卡 ----
let phase = CITY.defaultPhase;
let actionsDone = true;
const photo = new PhotoSystem({ ...CITY, renderer, scene, camera, pipeline });
const city = setupCity(photo, CITY, {
  getPhase: () => phase,
  actionDone: () => actionsDone,
});

function setPhase(key) {
  phase = key;
  world.setPhase(key);
  applyPhase(CITY, key, { pipeline, renderer });
  document.querySelectorAll('[data-phase]').forEach((b) => b.classList.toggle('on', b.dataset.phase === key));
}

// ---- 界面 ----
document.getElementById('city-name').textContent = `${CITY.name} · ${CITY.story}`;
document.querySelectorAll('[data-city]').forEach((a) => {
  a.classList.toggle('on', a.dataset.city === cityId);
  const q = new URLSearchParams(location.search);
  q.set('city', a.dataset.city);
  q.delete('pipeline');
  a.href = `?${q}`;
});
const phaseBox = document.getElementById('phases');
for (const [k, ph] of Object.entries(CITY.phases)) {
  const b = document.createElement('button');
  b.dataset.phase = k;
  b.textContent = ph.label;
  b.addEventListener('click', () => setPhase(k));
  phaseBox.appendChild(b);
}
const spotBox = document.getElementById('spots');
function renderSpots() {
  spotBox.innerHTML = '';
  for (const d of CITY.spotDefs) {
    const found = city.spots.some((s) => s.id === d.id);
    const row = document.createElement('div');
    row.className = `spot-row${city.book.has(d.id) ? ' got' : ''}${found ? '' : ' missing'}`;
    row.innerHTML = `<span class="code">${d.code}</span><span class="name">${d.label}</span><span class="kind">${d.required ? '必拍' : '可选'}</span>`;
    if (found && world.viewpoints[d.id]) {
      const go = document.createElement('button');
      go.textContent = '去这里';
      go.addEventListener('click', () => goto(d.id));
      row.appendChild(go);
    }
    row.title = `${d.story}\n建议：${d.suggest ?? ''}\n点位名：${d.anchor}`;
    spotBox.appendChild(row);
  }
}
renderSpots();
document.getElementById('actions').addEventListener('change', (e) => (actionsDone = e.target.checked));
document.getElementById('clear-stamps').addEventListener('click', () => {
  city.book.clear();
  renderSpots();
});

const toast = document.querySelector('.toast');
function say(msg, canvas) {
  toast.replaceChildren();
  if (canvas) {
    canvas.className = 'toast-stamp';
    toast.appendChild(canvas);
  }
  toast.append(msg);
  toast.style.display = 'flex';
  clearTimeout(say.t);
  say.t = setTimeout(() => (toast.style.display = 'none'), 3800);
}
photo.addEventListener('stamp', (e) => {
  const { spot, first, canvas } = e.detail;
  say(first ? `「${spot.label}」盖上了一枚章。${spot.bookmark ?? ''}` : `「${spot.label}」这枚章已经有了。`, first ? canvas : null);
  renderSpots();
});
photo.addEventListener('stampwait', (e) => say(`拍到了「${e.detail.spot.label}」，但还没完成那里的事（${e.detail.spot.story}）。`));
photo.addEventListener('photo', (e) => {
  const { saved, persistent, overLimit, record } = e.detail;
  if (record.meta.spotHits.length) return;
  if (!saved || !persistent) say('这个浏览器不能保存照片，记得在相册里下载。');
  else if (overLimit) say('相册已满 30 张，删掉几张吧。');
});
photo.addEventListener('error', (e) => say(e.detail.message));
photo.addEventListener('stylechange', (e) =>
  document.querySelectorAll('[data-style]').forEach((b) => b.classList.toggle('on', b.dataset.style === e.detail.styleId)),
);
document.querySelectorAll('[data-style]').forEach((b) => b.addEventListener('click', () => photo.setStyle(b.dataset.style)));
document.querySelectorAll('[data-style]').forEach((b) => b.classList.toggle('on', b.dataset.style === photo.styleId));

// ---- 简单的第一人称走动（正式版换成第三人称人物控制）----
const keys = new Set();
addEventListener('keydown', (e) => keys.add(e.code));
addEventListener('keyup', (e) => keys.delete(e.code));
let yaw = world.spawn.yaw;
let pitch = 0;
camera.position.set(world.spawn.pos[0], 0, world.spawn.pos[1]);
let drag = null;
renderer.domElement.addEventListener('pointerdown', (e) => (drag = [e.clientX, e.clientY]));
addEventListener('pointerup', () => (drag = null));
addEventListener('pointermove', (e) => {
  if (!drag) return;
  const k = 0.004 * photo.lookScale; // 长焦时转得慢一点
  yaw -= (e.clientX - drag[0]) * k;
  pitch = THREE.MathUtils.clamp(pitch - (e.clientY - drag[1]) * k, -1.2, 1.2);
  drag = [e.clientX, e.clientY];
});
addEventListener('resize', () => {
  renderer.setSize(innerWidth, innerHeight);
  if (!photo.active) {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
  } else photo.relayout();
});

// 去某个打卡点的参考机位，并按建议设好焦段、横竖、低角度、时段（测试和审图用）
function goto(id, { enter = true } = {}) {
  const v = world.viewpoints[id];
  if (!v) return;
  if (v.phase && v.phase !== phase) setPhase(v.phase);
  if (photo.active) photo.exit();
  camera.position.set(v.pos[0], 0, v.pos[1]);
  const eyeY = world.heightAt(v.pos[0], v.pos[1]) + world.eye;
  const dx = v.at[0] - v.pos[0];
  const dz = v.at[2] - v.pos[1];
  yaw = Math.atan2(-dx, -dz);
  pitch = Math.atan2(v.at[1] - eyeY, Math.hypot(dx, dz));
  camera.position.y = eyeY;
  camera.rotation.set(pitch, yaw, 0, 'YXZ');
  camera.updateMatrixWorld();
  if (enter) {
    photo.enter();
    photo.setFocal(Math.max(0, photo.focalLengths.indexOf(v.focal)));
    photo.setPortrait(!!v.portrait);
    photo.setLow(!!v.low);
    if (v.ev) photo.setEv(v.ev);
  }
}
window.photo = photo; // 方便在控制台测试
window.goto = goto;
window.cityKit = { city, CITY, setPhase, stampFor: (id) => stampFor(CITY, id) };

setPhase(phase);
const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.05);
  if (!photo.active) {
    // 取景时人物停下，只能转视角
    const f = (keys.has('KeyW') ? 1 : 0) - (keys.has('KeyS') ? 1 : 0);
    const s = (keys.has('KeyD') ? 1 : 0) - (keys.has('KeyA') ? 1 : 0);
    const speed = (keys.has('ShiftLeft') ? 12 : 3.2) * dt;
    camera.position.x += (-Math.sin(yaw) * f + Math.cos(yaw) * s) * speed;
    camera.position.z += (-Math.cos(yaw) * f - Math.sin(yaw) * s) * speed;
    world.clamp?.(camera.position);
  }
  camera.position.y = world.heightAt(camera.position.x, camera.position.z) + world.eye;
  camera.rotation.set(pitch, yaw, 0, 'YXZ');
  photo.updateLevel();
  if (pipeline instanceof HdrPipeline) pipeline.time = performance.now() % 1000;
  if (!photo.render()) pipeline.render(scene, camera);
});
