import * as THREE from 'three';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { Environment, TIME_PRESETS } from './environment.js';
import { createBridgeLamps } from './lights.js';
import { applyMaterials, createMaterials } from './materials.js';
import { Player } from './player.js';
import { createPost } from './post.js';
import { TextureLibrary } from './textures.js';
import { createTrees } from './vegetation.js';

const params = new URLSearchParams(window.location.search);
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
const environment = new Environment(renderer, scene, camera, quality);
const post = createPost(renderer, scene, camera, quality);

const manager = new THREE.LoadingManager();
manager.onProgress = (_url, loaded, total) => setStatus(`载入材质 ${loaded}/${total}`);
const library = new TextureLibrary(renderer, manager);
const materials = createMaterials(library, environment.csm, landcover);
const lamps = createBridgeLamps(meta.bridgeLamps);
scene.add(lamps.mesh);

try {
  setStatus('载入场景模型…');
  const draco = new DRACOLoader().setDecoderPath('./vendor/three/examples/jsm/libs/draco/');
  const gltf = await new GLTFLoader().setDRACOLoader(draco).loadAsync('./data/blockout.glb');
  draco.dispose();
  const missing = applyMaterials(gltf.scene, materials);
  if (missing.length) console.warn('No web material for:', missing);
  scene.add(gltf.scene);
  if (params.get('trees') !== '0') { // trees=0: performance comparison without vegetation
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

async function setTime(name) {
  const preset = await environment.apply(name);
  materials.setNight(preset.night);
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
const startTime = TIME_PRESETS[params.get('time')] ? params.get('time') : 'golden';
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
document.getElementById('credit').textContent = meta.attribution;

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
status?.remove();

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  post.setSize(window.innerWidth, window.innerHeight);
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
  player.update(dt);
  player.applyTo(camera);
  environment.update(dt);
  post.composer.render(dt);

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
