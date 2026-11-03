import * as THREE from 'three';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { Environment, TIME_PRESETS } from './environment.js';
import { createBridgeLamps } from './lights.js';
import { applyMaterials, createMaterials } from './materials.js';
import { Player } from './player.js';
import { createGoogleTiles } from './tiles.js';
import { createPost } from './post.js';
import { TextureLibrary } from './textures.js';
import { createTrees } from './vegetation.js';
import { PhotoSystem } from './cijian/photo/index.js';
import { SYDNEY, setupSydney, createSydneyPipeline } from './cijian/photo/presets/index.js';
import { NoahDay1, loadNoahAnchors } from './noah.js';

const params = new URLSearchParams(window.location.search);

// Our own meshes that the Google photogrammetry replaces in hybrid mode. The water, the walk-zone
// collision, the bridge lamps and the sky stay ours.
const REPLACED_BY_PHOTOGRAMMETRY = ['Buildings', 'Ground', 'HarbourBridge', 'OperaHouse'];

/** web/config.local.js (git-ignored) holds the Google Maps API key; see config.example.js. */
async function loadConfig() {
  try {
    return (await import('../config.local.js')).default ?? {};
  } catch {
    return {};
  }
}
const quality = params.get('q') === 'low' ? 'low' : 'high';
const status = document.getElementById('loading');
const setStatus = (text) => { if (status) status.textContent = text; };

async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  return res.json();
}

const [meta, landcover] = await Promise.all([
  fetchJson('./data/scene_meta.json'),
  fetchJson('./assets/ground/landcover.json'),
]);

const renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, quality === 'low' ? 1 : 1.5));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.info.autoReset = false; // count the whole frame (shadows, water reflection, passes), not the last pass
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.5, 45000);
const environment = new Environment(renderer, scene, camera, quality, landcover.extent);
const post = createPost(renderer, scene, camera, quality);

const manager = new THREE.LoadingManager();
manager.onProgress = (_url, loaded, total) => setStatus(`载入材质 ${loaded}/${total}`);
const library = new TextureLibrary(renderer, manager);
const materials = createMaterials(library, environment.csm, landcover);
const lamps = createBridgeLamps(meta.bridgeLamps);
scene.add(lamps.mesh);

const config = await loadConfig();
// layers=hybrid: Google photogrammetry for the city, ours for water, sky, lighting and walking.
// layers=own: everything from our own models (works offline and without a key).
const layerMode = params.get('layers') ?? (config.googleMapsApiKey ? 'hybrid' : 'own');
let googleTiles = null;
let blockoutRoot = null;

try {
  setStatus('载入场景模型…');
  const draco = new DRACOLoader().setDecoderPath('./vendor/three/examples/jsm/libs/draco/');
  const gltf = await new GLTFLoader().setDRACOLoader(draco).loadAsync('./data/blockout.glb');
  const missing = applyMaterials(gltf.scene, materials).filter((name) => name !== 'water_mask');
  if (missing.length) console.warn('No web material for:', missing);
  scene.add(gltf.scene);
  blockoutRoot = gltf.scene;
  const waterMask = gltf.scene.getObjectByName('WaterMask');
  if (waterMask) waterMask.visible = false;

  if (layerMode === 'hybrid') {
    if (!config.googleMapsApiKey) throw new Error('混合模式需要 Google Maps API Key：见 web/config.example.js');
    setStatus('连接 Google 实景三维…');
    googleTiles = createGoogleTiles({
      apiKey: config.googleMapsApiKey, origin: meta.origin, renderer, camera, draco,
    });
    scene.add(googleTiles.group);
    scene.updateMatrixWorld(true);
    if (waterMask) googleTiles.flattenWater(waterMask);
    for (const name of REPLACED_BY_PHOTOGRAMMETRY) {
      const obj = gltf.scene.getObjectByName(name);
      if (obj) obj.visible = false;
    }
  } else {
    draco.dispose();
  }
  if (layerMode !== 'hybrid' && params.get('trees') !== '0') { // trees=0: perf comparison
    setStatus('种树…');
    const trees = await createTrees(environment.csm);
    scene.add(trees.group);
  }
} catch (err) {
  setStatus(`场景载入失败：${err.message}`);
  throw err;
}

const player = new Player(meta, renderer.domElement);
player.setView('spawn');

let currentTime = 'golden';
async function setTime(name) {
  currentTime = name;
  document.querySelectorAll('[data-time]').forEach((b) => b.classList.toggle('on', b.dataset.time === name));
  const preset = await environment.apply(name);
  googleTiles?.setTint(preset.tileTint ?? 0xffffff);
  materials.setTimeOfDay({ night: preset.night, interior: preset.interior });
  lamps.setNight(preset.night);
  post.setBloom(preset.bloom);
}

function bindButtons(attr, handler) {
  const buttons = document.querySelectorAll(`[data-${attr}]`);
  for (const btn of buttons) {
    btn.addEventListener('click', () => {
      buttons.forEach((b) => b.classList.toggle('on', b === btn));
      handler(btn.dataset[attr]);
    });
  }
}
bindButtons('time', setTime);
bindButtons('view', (name) => player.setView(name));

// Reference-matching camera for calibration, e.g. ?cam=-470,90,280&look=0,30,30&fov=24&time=day&hud=0
// still=1 freezes the water so renders can be diffed pixel by pixel.
const vec = (key) => params.get(key)?.split(',').map(Number);
// quest=0: 只看风景，不跑 Noah 的任务线
const questOn = params.get('quest') !== '0' && !params.has('cam');
const startTime = TIME_PRESETS[params.get('time')] ? params.get('time') : (questOn ? 'day' : 'golden');
document.querySelectorAll('[data-time]').forEach((b) => b.classList.toggle('on', b.dataset.time === startTime));
await setTime(startTime);
if (params.has('cam')) {
  player.pos.set(...vec('cam'));
  player.mode = 'fly';
}
if (params.has('look')) player.lookAt(vec('look'));
if (params.has('fov')) camera.fov = Number(params.get('fov'));
camera.updateProjectionMatrix();
if (params.get('still') === '1') environment.waterSpeed = 0;
if (params.get('hud') === '0') {
  document.querySelectorAll('.hud, .hint, .stats, .credit').forEach((el) => { el.style.display = 'none'; });
}
const credit = document.getElementById('credit');
const updateCredit = () => {
  credit.textContent = googleTiles ? `${googleTiles.attribution()} · ${meta.attribution}` : meta.attribution;
};
updateCredit();
if (googleTiles) setInterval(updateCredit, 1000); // data credits follow the tiles in view

// bench=1: window.__bench(frames) renders synchronously and waits for the GPU, so it measures real
// frame cost even when the browser throttles requestAnimationFrame in a background window
if (params.get('bench') === '1') {
  // Reading a pixel back forces the GPU to finish (gl.finish alone does not block under ANGLE)
  const sync = () => {
    const gl = renderer.getContext();
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4));
  };
  window.__bench = (frames = 20) => {
    player.applyTo(camera);
    environment.update(0);
    post.composer.render(0);
    sync();
    const t0 = performance.now();
    for (let i = 0; i < frames; i++) {
      environment.update(0.016);
      post.composer.render(0.016);
      sync();
    }
    return (performance.now() - t0) / frames;
  };
}
// ---- 拍照（app-photo 分支的 cijian 拍照模块）和 Noah 第一天 ----
// camera=instant|rangefinder：图书馆里选的相机，默认 Noah 推荐的胶片旁轴
const pipeline = await createSydneyPipeline(renderer, scene, camera, { composer: post.composer });
const photo = new PhotoSystem({
  ...SYDNEY, renderer, scene, camera, pipeline,
  styleId: ['instant', 'rangefinder'].includes(params.get('camera')) ? params.get('camera') : SYDNEY.styleId,
});
let quest = null;
if (questOn) {
  setStatus('布置前景…');
  const { data: anchorData, usingProps } = await loadNoahAnchors(meta, player, scene);
  if (!usingProps) console.info('[Noah] 还没有 5060 的前景道具，先用出生点附近的临时点位');
  quest = new NoahDay1({ photo, player, scene, anchors: anchorData, setTime, getTime: () => currentTime });
  setupSydney(photo, {
    anchors: anchorData,
    getPhase: () => currentTime,
    actionDone: quest.actionDone,
    getChoice: quest.getChoice,
    // Maya 还没有 3D 模型：合影先不要求她入镜，问过“可以拍吗”就算
    overrides: { sy_cafe: { needSubjects: [] } },
  });
} else {
  setupSydney(photo, { anchors: { anchors: { ANCHOR_photo_opera: [0, 30, 0], ANCHOR_photo_bridge: [-401, 70, -513], ANCHOR_photo_bluehour: [-401, 70, -513] } }, getPhase: () => currentTime });
}
document.querySelectorAll('.hud, .hint, .stats, .credit').forEach((e) => { e.dataset.hud = ''; });
// 远景地标按真实模型判定（点在楼里面会被楼自己挡住）；遮挡只算实心的场景，不算透明叶片的卡片树
const landmarkObjects = { sy_opera: 'OperaHouse', sy_bridge: 'HarbourBridge', sy_bluehour: 'HarbourBridge' };
for (const spot of photo.spots) {
  const obj = landmarkObjects[spot.id] && blockoutRoot?.getObjectByName(landmarkObjects[spot.id]);
  if (obj) spot.target = obj;
}
if (blockoutRoot) photo.occluders = [blockoutRoot];
if (params.get('debug') === '1') window.__cijian = { photo, quest, player, setTime }; // 测试用
status?.remove();

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  post.setSize(window.innerWidth, window.innerHeight);
  googleTiles?.setSize(camera, renderer);
  environment.csm.updateFrustums();
});

const stats = document.getElementById('stats');
const clock = new THREE.Clock();
let frames = 0;
let fpsStart = performance.now();
environment.csm.updateFrustums();

renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.1);
  renderer.info.reset();
  // 取景、对白、地图页打开时人物不走；取景时视角灵敏度跟着焦段变慢
  player.lookScale = photo.active ? photo.lookScale : 1;
  if (!photo.active && !quest?.blocking) player.update(dt);
  player.applyTo(camera);
  quest?.update(clock.elapsedTime);
  camera.updateMatrixWorld();
  googleTiles?.update();
  environment.update(dt);
  if (!photo.render()) pipeline.render(scene, camera);

  // Measure fps from wall-clock time: dt is clamped, so it would overstate slow frame rates
  frames += 1;
  const now = performance.now();
  if (now - fpsStart > 500) {
    const { calls, triangles } = renderer.info.render;
    const p = player.pos;
    stats.textContent = `${Math.round((frames * 1000) / (now - fpsStart))} fps  ${calls} draws  ${(triangles / 1000).toFixed(0)}k tris  ${quality}\n`
      + `x ${p.x.toFixed(0)}  y ${p.y.toFixed(1)}  z ${p.z.toFixed(0)}  ${player.mode}`;
    frames = 0;
    fpsStart = now;
  }
});
