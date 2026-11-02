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
import { makePerson } from './test-scenes/people.js';

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
world.npcs?.forEach((n) => (n.position.y = world.heightAt(n.position.x, n.position.z))); // 站在台阶上的人贴到台阶面
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

// ---- 玩家人物（占位人形；东京是凛，悉尼是 Noah）。测试页是第一人称，人物站在镜头的位置 ----
const avatar = makePerson(
  cityId === 'sydney'
    ? { name: 'PLAYER_noah', color: 0xb8643a, hair: 0x9a6a3a, height: 1.82 }
    : { name: 'PLAYER_rin', color: 0x2f3c56, hair: 0x1a1512, height: 1.62 },
);
scene.add(avatar);

// ---- 拍照模块：城市配置直接展开，再一步接好打卡点、人物和回忆卡 ----
let phase = CITY.defaultPhase;
let actionsDone = true;
const photo = new PhotoSystem({ ...CITY, renderer, scene, camera, pipeline });
const city = setupCity(photo, CITY, {
  getPhase: () => phase,
  actionDone: () => actionsDone,
  avatar,
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
// 征得同意：剧情里问过“可以拍吗”之后宿主调 photo.setConsent(id)
const askable = photo.subjects.filter((s) => s.needsConsent);
document.getElementById('consent-names').textContent = askable.map((s) => s.label).join('、') || '（无）';
document.getElementById('consent').addEventListener('change', (e) => askable.forEach((s) => photo.setConsent(s.id, e.target.checked)));
document.getElementById('timer-btn').addEventListener('click', () => (photo.timerRunning ? photo.cancelTimer() : photo.startTimer()));
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
photo.addEventListener('consentwait', (e) => say(`照片留下了，但没问过 ${e.detail.labels.join('、')}，这张不算进剧情。先问一声“可以拍吗”。`));
photo.addEventListener('subjectwait', (e) => {
  const names = e.detail.missing.map((id) => photo.subjects.find((s) => s.id === id)?.label ?? id);
  say(`「${e.detail.spot.label}」要拍到 ${names.join('、')}。`);
});
photo.addEventListener('photo', (e) => {
  const { saved, persistent, overLimit, record } = e.detail;
  const m = record.meta;
  const who = m.subjectsInFrame.map((p) => p.label).join('、');
  document.getElementById('last-shot').textContent = `上一张：${m.selfie ? '定时自拍 · ' : ''}入镜 ${who || '无人'}${m.storyOk ? '' : '（有人没问过）'}`;
  if (m.spotHits.length || !m.storyOk) return;
  if (!saved || !persistent) say('这个浏览器不能保存照片，记得在相册里下载。');
  else if (overLimit) say('相册已满 30 张，删掉几张吧。');
});
photo.addEventListener('error', (e) => say(e.detail.message));
photo.addEventListener('stylechange', (e) =>
  document.querySelectorAll('[data-style]').forEach((b) => b.classList.toggle('on', b.dataset.style === e.detail.styleId)),
);
document.querySelectorAll('[data-style]').forEach((b) => b.addEventListener('click', () => photo.setStyle(b.dataset.style)));
document.querySelectorAll('[data-style]').forEach((b) => b.classList.toggle('on', b.dataset.style === photo.styleId));

// ---- 定时自拍：相机留在原地；人物自己走到建议站位、面向相机，玩家也可以用 WASD 挪位置 ----
const tripod = { stand: null, look: null, manual: false, yaw: 0 };
photo.addEventListener('selftimer:start', (e) => {
  tripod.stand = e.detail.standAt;
  tripod.look = e.detail.lookAt;
  tripod.manual = false;
  tripod.yaw = yaw;
  // 人从相机旁边、画面外起步，走进画面（不从镜头里面钻出来）
  const fwd = new THREE.Vector3(-Math.sin(yaw), 0, -Math.cos(yaw));
  const right = new THREE.Vector3(-fwd.z, 0, fwd.x);
  avatar.position.set(camera.position.x, world.heightAt(camera.position.x, camera.position.z), camera.position.z);
  avatar.position.addScaledVector(right, 1.1).addScaledVector(fwd, -0.2);
  avatar.userData.person.play('walk');
});
photo.addEventListener('selftimer:tick', (e) => {
  if (e.detail.remaining <= 3) avatar.userData.person.play('pose_photo'); // 剩 3 秒摆姿势
});
photo.addEventListener('selftimer:fire', () => avatar.userData.person.play('pose_photo'));
function afterTimer() {
  // 拍完：玩家回到人物站的地方，转身看向刚才放相机的位置
  avatar.userData.person.play('idle');
  camera.position.x = avatar.position.x;
  camera.position.z = avatar.position.z;
  if (tripod.look) yaw = Math.atan2(-(tripod.look.x - avatar.position.x), -(tripod.look.z - avatar.position.z));
  pitch = 0;
  tripod.stand = null;
  photo.exit();
}
photo.addEventListener('selftimer:end', () => setTimeout(afterTimer, 900)); // 留一下“咔嚓”之后的画面
photo.addEventListener('selftimer:cancel', () => setTimeout(afterTimer, 0));

function updateTimerWalk(dt) {
  const p = avatar.position;
  const f = (keys.has('KeyW') ? 1 : 0) - (keys.has('KeyS') ? 1 : 0);
  const s = (keys.has('KeyD') ? 1 : 0) - (keys.has('KeyA') ? 1 : 0);
  let mx = 0;
  let mz = 0;
  if (f || s) {
    // 手动挪：方向按三脚架相机的朝向算（W = 离相机更远）
    tripod.manual = true;
    mx = -Math.sin(tripod.yaw) * f + Math.cos(tripod.yaw) * s;
    mz = -Math.cos(tripod.yaw) * f - Math.sin(tripod.yaw) * s;
  } else if (!tripod.manual && tripod.stand) {
    mx = tripod.stand.x - p.x;
    mz = tripod.stand.z - p.z;
    if (Math.hypot(mx, mz) < 0.05) mx = mz = 0;
  }
  const len = Math.hypot(mx, mz);
  const person = avatar.userData.person;
  if (len > 0) {
    const step = Math.min(len, 1.6 * walkDt) / len;
    p.x += mx * step;
    p.z += mz * step;
    if (person.pose !== 'pose_photo') person.play('walk');
    avatar.rotation.y = Math.atan2(mx, mz);
  } else {
    if (person.pose === 'walk') person.play('idle');
    if (tripod.look) avatar.rotation.y = Math.atan2(tripod.look.x - p.x, tripod.look.z - p.z); // 站定后面向相机
  }
  p.y = world.heightAt(p.x, p.z);
}

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
window.avatar = avatar;
window.goto = goto;
window.cityKit = { city, CITY, setPhase, stampFor: (id) => stampFor(CITY, id) };

setPhase(phase);
const clock = new THREE.Clock();
let walkDt = 0;
let lastT = 0;
function frame() {
  const dt = Math.min(clock.getDelta(), 0.05);
  walkDt = Math.min(clock.elapsedTime - lastT, 1); // 走路按真实时间算，帧率低时人也能按时走到位
  lastT = clock.elapsedTime;
  if (photo.timerRunning) updateTimerWalk(dt);
  else if (!photo.active) {
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
  if (!photo.timerRunning) {
    // 平时人物跟着镜头（第一人称：镜头就在人物头的位置，从里面看不见自己的模型）
    avatar.position.set(camera.position.x, camera.position.y - world.eye, camera.position.z);
    avatar.rotation.y = yaw + Math.PI;
  }
  avatar.userData.person.update(dt);
  world.npcs?.forEach((n) => n.userData.person.update(dt));
  photo.updateLevel();
  if (pipeline instanceof HdrPipeline) pipeline.time = performance.now() % 1000;
  if (!photo.render()) pipeline.render(scene, camera);
}
renderer.setAnimationLoop(frame);
window.frame = frame; // 浏览器面板在后台时动画会停，测试脚本可以手动推帧
