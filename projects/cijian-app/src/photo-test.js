// 拍照模块的独立测试页：一条程序生成的小街，代替还没烘焙好的东京场景。
// 正式接入时只需要照着这里的 3 处调用（创建、每帧 render、移动时判断 active）。
//
// 画面管线默认用烘焙小样的那一套（HDR → 泛光 → 曝光 → AgX 查找表），查找表文件从
//   test-data/lut_morning.bin、test-data/lut_sunset.bin 读（就是 cijian-5070/web/data 里的同名文件，
//   不入库，见 README）。读不到就退回 StandardPipeline（ACES）。?pipeline=standard 可强制用后者。
import * as THREE from 'three';
import { PhotoSystem, HdrPipeline, StandardPipeline } from './photo/index.js';

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.prepend(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, 0.1, 400);
camera.position.set(0, 1.6, 14);

// ---- 灯光和两个时段 ----
const hemi = new THREE.HemisphereLight(0xbcd3ff, 0x6b5a48, 1.2);
const sun = new THREE.DirectionalLight(0xffffff, 3);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -30, right: 30, top: 30, bottom: -30, far: 120 });
scene.add(hemi, sun, sun.target);
// exposure 是 game.js 里的 EV（实际倍数 2^exposure），bloom 同 game.js
const PHASES = {
  day: { sky: 0x9cc4ea, skyI: 1.6, fog: 0xbcd3ea, sun: 0xfff4e0, sunI: 4.0, hemiI: 1.1, pos: [20, 40, 10], exposure: 0.5, bloom: 0, lut: 0, std: 1.0 },
  sunset: { sky: 0xe39a6c, skyI: 1.2, fog: 0xd99573, sun: 0xffa45c, sunI: 7.5, hemiI: 0.45, pos: [-40, 7, -10], exposure: 0.3, bloom: 0.2, lut: 1, std: 1.15 },
};
let phase = 'day';
let pipeline;
function setPhase(p) {
  phase = p;
  const c = PHASES[p];
  scene.background = new THREE.Color(c.sky).multiplyScalar(c.skyI);
  scene.fog = new THREE.Fog(c.fog, 25, 120);
  sun.color.set(c.sun);
  sun.intensity = c.sunI;
  hemi.intensity = c.hemiI;
  sun.position.set(...c.pos);
  if (pipeline instanceof HdrPipeline) {
    pipeline.exposure = Math.pow(2, c.exposure);
    pipeline.bloom = c.bloom;
    pipeline.lutMix = c.lut;
  } else {
    renderer.toneMappingExposure = c.std;
  }
  document.querySelectorAll('[data-phase]').forEach((b) => b.classList.toggle('on', b.dataset.phase === p));
}

async function makePipeline() {
  if (new URLSearchParams(location.search).get('pipeline') !== 'standard') {
    try {
      const hdr = new HdrPipeline(renderer);
      const [a, b] = await Promise.all([hdr.loadLut('test-data/lut_morning.bin'), hdr.loadLut('test-data/lut_sunset.bin')]);
      hdr.setLuts(a, b);
      return hdr;
    } catch (e) {
      console.warn('读不到查找表，改用 StandardPipeline', e);
    }
  }
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  return new StandardPipeline(renderer);
}
pipeline = await makePipeline();
document.getElementById('pipe-info').textContent =
  pipeline instanceof HdrPipeline ? '画面管线：烘焙小样同款（泛光 + AgX）' : '画面管线：Three.js ACES';

// ---- 一条小街：路、两排房子、暖帘、灯笼、电线杆、台阶 ----
const rand = mulberry32(7);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.MeshStandardMaterial({ color: 0x5d5a55, roughness: 0.95 }));
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);
const road = new THREE.Mesh(new THREE.PlaneGeometry(5, 70), new THREE.MeshStandardMaterial({ color: 0x8a8278, roughness: 0.85 }));
road.rotation.x = -Math.PI / 2;
road.position.y = 0.01;
road.receiveShadow = true;
scene.add(road);

const wallColors = [0xd9cbb3, 0xb9a68a, 0x8d7b67, 0xe8e0d0, 0x6f5f52, 0xc7b8a0];
const norenColors = [0x23395b, 0x7a2a1f, 0x2f4a3a, 0x3a2f45];
for (const side of [-1, 1]) {
  let z = -30;
  while (z < 30) {
    const w = 4 + rand() * 3;
    const h = 5 + rand() * 4;
    const d = 6;
    const house = new THREE.Mesh(
      new THREE.BoxGeometry(d, h, w),
      new THREE.MeshStandardMaterial({ color: wallColors[Math.floor(rand() * wallColors.length)], roughness: 0.9 }),
    );
    house.position.set(side * (2.5 + 1 + d / 2), h / 2, z + w / 2);
    house.castShadow = house.receiveShadow = true;
    scene.add(house);
    const roof = new THREE.Mesh(new THREE.BoxGeometry(d + 0.6, 0.25, w + 0.3), new THREE.MeshStandardMaterial({ color: 0x3b3a3c, roughness: 0.7 }));
    roof.position.set(house.position.x, h + 0.12, house.position.z);
    roof.castShadow = true;
    scene.add(roof);
    // 店面：深色门洞 + 暖帘 + 雨棚
    const front = side * (2.5 + 1);
    const door = new THREE.Mesh(new THREE.PlaneGeometry(w * 0.7, 2.4), new THREE.MeshStandardMaterial({ color: 0x241c16, roughness: 0.4, emissive: 0x3a2410, emissiveIntensity: 0.6 }));
    door.position.set(front - side * 0.01, 1.2, z + w / 2);
    door.rotation.y = -side * Math.PI / 2;
    scene.add(door);
    const noren = new THREE.Mesh(new THREE.PlaneGeometry(w * 0.6, 0.9), new THREE.MeshStandardMaterial({ color: norenColors[Math.floor(rand() * norenColors.length)], side: THREE.DoubleSide, roughness: 1 }));
    noren.position.set(front - side * 0.06, 2.05, z + w / 2);
    noren.rotation.y = -side * Math.PI / 2;
    noren.castShadow = true;
    scene.add(noren);
    const awning = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.06, w * 0.9), new THREE.MeshStandardMaterial({ color: 0x9a3b2c, roughness: 0.8 }));
    awning.position.set(front - side * 0.6, 2.7, z + w / 2);
    awning.rotation.z = side * 0.25;
    awning.castShadow = true;
    scene.add(awning);
    if (rand() > 0.5) {
      const lantern = new THREE.Mesh(new THREE.SphereGeometry(0.28, 16, 12), new THREE.MeshStandardMaterial({ color: 0xd8432c, emissive: 0xff6a3a, emissiveIntensity: 1.4 }));
      lantern.scale.y = 1.35;
      lantern.position.set(front - side * 0.9, 2.3, z + 0.6);
      scene.add(lantern);
    }
    z += w + 0.15;
  }
}
for (let z = -28; z <= 28; z += 14) {
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.15, 8, 10), new THREE.MeshStandardMaterial({ color: 0x8f8a83 }));
  pole.position.set(2.8, 4, z);
  pole.castShadow = true;
  scene.add(pole);
}
// 街尾的台阶（也是测试用的打卡点）
const steps = new THREE.Group();
steps.name = 'steps';
scene.add(steps);
for (let i = 0; i < 12; i++) {
  const step = new THREE.Mesh(new THREE.BoxGeometry(5, 0.18 * (i + 1), 0.4), new THREE.MeshStandardMaterial({ color: 0x9d968b, roughness: 0.9 }));
  step.position.set(0, (0.18 * (i + 1)) / 2, -31 - i * 0.4);
  step.castShadow = step.receiveShadow = true;
  steps.add(step);
}
// 交互点标记：只在游戏里看得到，照片里不出现
const marker = new THREE.Mesh(new THREE.TorusGeometry(0.5, 0.04, 8, 40), new THREE.MeshBasicMaterial({ color: 0xfff1b8 }));
marker.rotation.x = -Math.PI / 2;
marker.position.set(0, 0.05, 6);
marker.userData.hideInPhoto = true;
scene.add(marker);

// ---- 拍照模块 ----
const photo = new PhotoSystem({
  renderer,
  scene,
  camera,
  pipeline,
  spots: [{ id: 'steps', target: steps, minCoverage: 0.03 }],
  getContext: () => ({ sceneId: 'photo-test', spotId: null, phase, weather: 'clear' }),
});
photo.album.cardInfo = (picked) => ({
  title: '寄给明天的声音',
  subtitle: '三日归途 · 第一天 · 东京',
  caption: `${new Date(picked[0].meta.createdAt).toLocaleDateString('zh-CN')} · 晴 · 谷中 · 留下了风铃的声音`,
});
const toast = document.querySelector('.toast');
function say(msg) {
  toast.textContent = msg;
  toast.style.display = 'block';
  clearTimeout(say.t);
  say.t = setTimeout(() => (toast.style.display = 'none'), 3500);
}
photo.addEventListener('photo', (e) => {
  const { saved, persistent, overLimit, record } = e.detail;
  if (record.meta.spotHits.includes('steps')) say('拍到了街尾的台阶，盖上一枚章。');
  else if (!saved || !persistent) say('这个浏览器不能保存照片，记得在相册里下载。');
  else if (overLimit) say('相册已满 30 张，删掉几张吧。');
});
photo.addEventListener('error', (e) => say(e.detail.message));
photo.addEventListener('stylechange', (e) =>
  document.querySelectorAll('[data-style]').forEach((b) => b.classList.toggle('on', b.dataset.style === e.detail.styleId)),
);
document.querySelectorAll('[data-style]').forEach((b) => b.addEventListener('click', () => photo.setStyle(b.dataset.style)));
document.querySelectorAll('[data-phase]').forEach((b) => b.addEventListener('click', () => setPhase(b.dataset.phase)));
document.querySelectorAll('[data-style]').forEach((b) => b.classList.toggle('on', b.dataset.style === photo.styleId));
setPhase('day');
window.photo = photo; // 方便在控制台测试

// ---- 简单的第一人称走动（正式版换成第三人称人物控制）----
const keys = new Set();
addEventListener('keydown', (e) => keys.add(e.code));
addEventListener('keyup', (e) => keys.delete(e.code));
let yaw = 0;
let pitch = 0;
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
  }
});

const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.05);
  if (!photo.active) {
    // 取景时人物停下，只能转视角
    const f = (keys.has('KeyW') ? 1 : 0) - (keys.has('KeyS') ? 1 : 0);
    const s = (keys.has('KeyD') ? 1 : 0) - (keys.has('KeyA') ? 1 : 0);
    const speed = 3.2 * dt;
    camera.position.x += (-Math.sin(yaw) * f + Math.cos(yaw) * s) * speed;
    camera.position.z += (-Math.cos(yaw) * f - Math.sin(yaw) * s) * speed;
  }
  camera.rotation.set(pitch, yaw, 0, 'YXZ');
  marker.rotation.z += dt;
  photo.updateLevel();
  if (pipeline instanceof HdrPipeline) pipeline.time = performance.now() % 1000;
  if (!photo.render()) pipeline.render(scene, camera);
});

function mulberry32(a) {
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
