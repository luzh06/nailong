import * as THREE from 'three';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { Sky } from 'three/addons/objects/Sky.js';
import { Water } from 'three/addons/objects/Water.js';

const WALK_SPEED = 1.6;      // m/s
const MAX_SLOPE = Math.tan(THREE.MathUtils.degToRad(35)); // steeper ground blocks walking
const RUN_MULTIPLIER = 2.6;
const FLY_SPEED = 60.0;
const LOOK_SENSITIVITY = 0.0035;
const PITCH_LIMIT = Math.PI / 2 - 0.05;
let waterSpeed = 0.6;

// Sun azimuth is clockwise from north; elevation in degrees.
const TIME_PRESETS = {
  day: { azimuth: 20, elevation: 48, exposure: 0.5, turbidity: 2.5, rayleigh: 0.8, fog: 0xa9bdd0, fogDensity: 0.00008 },
  golden: { azimuth: 285, elevation: 6, exposure: 0.48, turbidity: 5, rayleigh: 1.8, fog: 0xe0ae80, fogDensity: 0.0001 },
  blue: { azimuth: 280, elevation: -3.5, exposure: 1.1, turbidity: 2, rayleigh: 3.0, fog: 0x34405a, fogDensity: 0.00014 },
};

const meta = await (await fetch('./data/scene_meta.json')).json();
const walkZone = meta.walkZone;

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.3, 40000);

const sunLight = new THREE.DirectionalLight(0xffffff, 2.5);
const hemiLight = new THREE.HemisphereLight(0xbfd4ff, 0x4a4036, 0.6);
scene.add(sunLight, hemiLight);

const sky = new Sky();
sky.scale.setScalar(30000);
scene.add(sky);

const water = new Water(new THREE.PlaneGeometry(40000, 40000), {
  textureWidth: 1024,
  textureHeight: 1024,
  waterNormals: makeWaterNormals(256),
  sunDirection: new THREE.Vector3(),
  sunColor: 0xffffff,
  waterColor: 0x0b2a3a,
  distortionScale: 2.2,
  fog: true,
});
water.rotation.x = -Math.PI / 2;
water.material.uniforms.size.value = 1.2;
scene.add(water);

const pmrem = new THREE.PMREMGenerator(renderer);
let envTarget = null;

function applyTime(name) {
  const p = TIME_PRESETS[name];
  const el = THREE.MathUtils.degToRad(p.elevation);
  const az = THREE.MathUtils.degToRad(p.azimuth);
  const sunDir = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el));

  const u = sky.material.uniforms;
  u.sunPosition.value.copy(sunDir);
  u.turbidity.value = p.turbidity;
  u.rayleigh.value = p.rayleigh;
  u.mieCoefficient.value = 0.005;
  u.mieDirectionalG.value = 0.8;
  water.material.uniforms.sunDirection.value.copy(sunDir).normalize();

  sunLight.position.copy(sunDir).multiplyScalar(1000);
  sunLight.intensity = Math.max(0, Math.sin(el)) * 3.0 + 0.15;
  sunLight.color.set(p.elevation < 10 ? 0xffc48a : 0xfff4e5);
  hemiLight.intensity = p.elevation < 0 ? 0.35 : 0.6;
  renderer.toneMappingExposure = p.exposure;
  scene.fog = new THREE.FogExp2(p.fog, p.fogDensity);

  // Bake the sky into an environment map so the PBR materials pick up its colour
  const skyScene = new THREE.Scene();
  const skyCopy = new Sky();
  skyCopy.scale.setScalar(1000);
  Object.assign(skyCopy.material.uniforms.sunPosition.value, sunDir);
  for (const key of ['turbidity', 'rayleigh', 'mieCoefficient', 'mieDirectionalG']) {
    skyCopy.material.uniforms[key].value = u[key].value;
  }
  skyScene.add(skyCopy);
  envTarget?.dispose();
  envTarget = pmrem.fromScene(skyScene);
  scene.environment = envTarget.texture;
}

// Tileable normal map built from layered sine waves, so no external texture is needed
function makeWaterNormals(size) {
  const data = new Uint8Array(size * size * 4);
  // Integer wave numbers keep the map tileable; a seeded spread of directions avoids visible stripes
  let seed = 7;
  const rand = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const waves = Array.from({ length: 24 }, (_, i) => {
    const k = 2 + i * 0.9;
    const angle = rand() * Math.PI * 2;
    return [Math.round(Math.cos(angle) * k), Math.round(Math.sin(angle) * k), 1 / (1 + i * 0.45), rand() * Math.PI * 2];
  });
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      let dx = 0;
      let dy = 0;
      for (const [kx, ky, amp, offset] of waves) {
        const phase = (2 * Math.PI * (kx * x + ky * y)) / size + offset;
        dx += amp * kx * Math.cos(phase);
        dy += amp * ky * Math.cos(phase);
      }
      const n = new THREE.Vector3(-dx * 0.03, -dy * 0.03, 1).normalize();
      const i = (y * size + x) * 4;
      data[i] = (n.x * 0.5 + 0.5) * 255;
      data[i + 1] = (n.y * 0.5 + 0.5) * 255;
      data[i + 2] = (n.z * 0.5 + 0.5) * 255;
      data[i + 3] = 255;
    }
  }
  const tex = new THREE.DataTexture(data, size, size);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.needsUpdate = true;
  return tex;
}

// ---------------------------------------------------------------- player

const player = { pos: new THREE.Vector3(...meta.views.spawn.pos), yaw: 0, pitch: 0, mode: 'walk' };
const keys = new Set();

function lookAt(target) {
  const d = new THREE.Vector3(...target).sub(player.pos);
  player.yaw = Math.atan2(-d.x, -d.z);
  player.pitch = Math.atan2(d.y, Math.hypot(d.x, d.z));
}

function insidePolygon(ring, x, z) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, zi] = ring[i];
    const [xj, zj] = ring[j];
    if ((zi > z) !== (zj > z) && x < ((xj - xi) * (z - zi)) / (zj - zi) + xi) inside = !inside;
  }
  return inside;
}

function insideWalkZone(x, z) {
  return insidePolygon(walkZone, x, z) && !meta.walkHoles.some((hole) => insidePolygon(hole, x, z));
}

// Bilinear lookup in the walk-zone height grid exported by build_blockout.py
function groundHeight(x, z) {
  const g = meta.ground;
  const fx = THREE.MathUtils.clamp((x - g.x0) / g.step, 0, g.nx - 1.001);
  const fz = THREE.MathUtils.clamp((z - g.z0) / g.step, 0, g.nz - 1.001);
  const ix = Math.floor(fx);
  const iz = Math.floor(fz);
  const tx = fx - ix;
  const tz = fz - iz;
  const h = (i, k) => g.h[(iz + k) * g.nx + ix + i];
  return (h(0, 0) * (1 - tx) + h(1, 0) * tx) * (1 - tz) + (h(0, 1) * (1 - tx) + h(1, 1) * tx) * tz;
}

function canStep(x, z, nx, nz) {
  if (!insideWalkZone(nx, nz)) return false;
  const run = Math.hypot(nx - x, nz - z);
  return run === 0 || Math.abs(groundHeight(nx, nz) - groundHeight(x, z)) / run <= MAX_SLOPE;
}

const VIEWS = {
  spawn: () => ({ ...meta.views.spawn, mode: 'walk' }),
  bridge: () => ({ ...meta.views.bridge, mode: 'walk' }),
  fly: () => ({ pos: [player.pos.x, 180, player.pos.z + 300], look: meta.anchors.opera_house, mode: 'fly' }),
};

function setView(name) {
  const v = VIEWS[name]();
  player.pos.set(...v.pos);
  player.mode = v.mode;
  lookAt(v.look);
  document.querySelectorAll('[data-view]').forEach((b) => b.classList.toggle('on', b.dataset.view === name));
}

function updatePlayer(dt) {
  const forward = new THREE.Vector3(-Math.sin(player.yaw), 0, -Math.cos(player.yaw));
  const right = new THREE.Vector3(-forward.z, 0, forward.x);
  const move = new THREE.Vector3();
  if (keys.has('KeyW')) move.add(forward);
  if (keys.has('KeyS')) move.sub(forward);
  if (keys.has('KeyD')) move.add(right);
  if (keys.has('KeyA')) move.sub(right);

  if (player.mode === 'fly') {
    if (keys.has('KeyE')) move.y += 1;
    if (keys.has('KeyQ')) move.y -= 1;
    const speed = FLY_SPEED * (keys.has('ShiftLeft') ? 4 : 1);
    player.pos.addScaledVector(move.normalize(), speed * dt);
    player.pos.y = Math.max(player.pos.y, 1.5);
    return;
  }
  if (move.lengthSq() === 0) return;
  const step = move.normalize().multiplyScalar(WALK_SPEED * (keys.has('ShiftLeft') ? RUN_MULTIPLIER : 1) * dt);
  const { x, z } = player.pos;
  // Slide along edges and steep ground instead of stopping dead
  if (canStep(x, z, x + step.x, z + step.z)) player.pos.set(x + step.x, player.pos.y, z + step.z);
  else if (canStep(x, z, x + step.x, z)) player.pos.x += step.x;
  else if (canStep(x, z, x, z + step.z)) player.pos.z += step.z;
  player.pos.y = groundHeight(player.pos.x, player.pos.z) + meta.eyeHeight;
}

let dragging = false;
renderer.domElement.addEventListener('pointerdown', (e) => { dragging = true; renderer.domElement.setPointerCapture(e.pointerId); });
renderer.domElement.addEventListener('pointerup', () => { dragging = false; });
renderer.domElement.addEventListener('pointermove', (e) => {
  if (!dragging) return;
  player.yaw -= e.movementX * LOOK_SENSITIVITY;
  player.pitch = THREE.MathUtils.clamp(player.pitch - e.movementY * LOOK_SENSITIVITY, -PITCH_LIMIT, PITCH_LIMIT);
});
window.addEventListener('keydown', (e) => keys.add(e.code));
window.addEventListener('keyup', (e) => keys.delete(e.code));
window.addEventListener('blur', () => keys.clear());
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

function bindButtons(attr, handler) {
  const buttons = document.querySelectorAll(`[data-${attr}]`);
  for (const btn of buttons) {
    btn.addEventListener('click', () => {
      buttons.forEach((b) => b.classList.toggle('on', b === btn));
      handler(btn.dataset[attr]);
    });
  }
}
bindButtons('time', applyTime);
bindButtons('view', setView);

// ---------------------------------------------------------------- load and run

try {
  const draco = new DRACOLoader().setDecoderPath('./vendor/three/examples/jsm/libs/draco/');
  const gltf = await new GLTFLoader().setDRACOLoader(draco).loadAsync('./data/blockout.glb');
  draco.dispose();
  gltf.scene.traverse((obj) => {
    if (obj.isMesh && obj.material.name.startsWith('opera_tile')) obj.material.side = THREE.DoubleSide;
  });
  scene.add(gltf.scene);
  document.getElementById('loading').remove();
} catch (err) {
  document.getElementById('loading').textContent = `模型载入失败：${err.message}`;
  throw err;
}

document.getElementById('credit').textContent = meta.attribution;
applyTime('golden');
setView('spawn');
applyDebugParams(new URLSearchParams(window.location.search));

// Reference-matching camera for calibration, e.g. ?cam=-470,90,280&look=0,30,30&fov=24&time=day&hud=0
function applyDebugParams(params) {
  const vec = (key) => params.get(key)?.split(',').map(Number);
  if (params.has('time')) applyTime(params.get('time'));
  if (params.has('cam')) {
    player.pos.set(...vec('cam'));
    player.mode = 'fly';
  }
  if (params.has('look')) lookAt(vec('look'));
  if (params.has('fov')) {
    camera.fov = Number(params.get('fov'));
    camera.updateProjectionMatrix();
  }
  // still=1 freezes the water animation so before/after renders can be diffed pixel by pixel
  if (params.get('still') === '1') waterSpeed = 0;
  if (params.get('hud') === '0') {
    document.querySelectorAll('.hud, .hint, .stats, .credit').forEach((el) => { el.style.display = 'none'; });
  }
}

const stats = document.getElementById('stats');
const clock = new THREE.Clock();
let frames = 0;
let fpsStart = performance.now();

renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.1);
  updatePlayer(dt);
  camera.position.copy(player.pos);
  camera.rotation.set(player.pitch, player.yaw, 0, 'YXZ');
  water.material.uniforms.time.value += dt * waterSpeed;
  renderer.render(scene, camera);

  // Measure fps from wall-clock time: dt is clamped, so it would overstate slow frame rates
  frames += 1;
  const now = performance.now();
  if (now - fpsStart > 500) {
    const { calls, triangles } = renderer.info.render;
    stats.textContent = `${Math.round((frames * 1000) / (now - fpsStart))} fps  ${calls} draws  ${(triangles / 1000).toFixed(0)}k tris\n`
      + `x ${player.pos.x.toFixed(0)}  y ${player.pos.y.toFixed(1)}  z ${player.pos.z.toFixed(0)}  ${player.mode}`;
    frames = 0;
    fpsStart = now;
  }
});
