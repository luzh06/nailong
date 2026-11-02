import * as THREE from 'three';

const WALK_SPEED = 1.6;      // m/s
const RUN_MULTIPLIER = 2.6;
const FLY_SPEED = 60.0;
const LOOK_SENSITIVITY = 0.0035;
const PITCH_LIMIT = Math.PI / 2 - 0.05;
const MAX_SLOPE = Math.tan(THREE.MathUtils.degToRad(35)); // steeper ground blocks walking
const FLY_FLOOR = 1.5;

function insidePolygon(ring, x, z) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, zi] = ring[i];
    const [xj, zj] = ring[j];
    if ((zi > z) !== (zj > z) && x < ((xj - xi) * (z - zi)) / (zj - zi) + xi) inside = !inside;
  }
  return inside;
}

/**
 * First-person walker confined to the foreshore walk zone, plus a free-flight mode (the basis for
 * a later helicopter ride). Modes: 'walk' | 'fly'.
 */
export class Player {
  constructor(meta, domElement) {
    this.meta = meta;
    this.pos = new THREE.Vector3(...meta.views.spawn.pos);
    this.yaw = 0;
    this.pitch = 0;
    this.mode = 'walk';
    this.keys = new Set();
    this.bindInput(domElement);
  }

  bindInput(el) {
    let dragging = false;
    el.addEventListener('pointerdown', (e) => { dragging = true; el.setPointerCapture(e.pointerId); });
    el.addEventListener('pointerup', () => { dragging = false; });
    el.addEventListener('pointermove', (e) => {
      if (!dragging) return;
      this.yaw -= e.movementX * LOOK_SENSITIVITY;
      this.pitch = THREE.MathUtils.clamp(this.pitch - e.movementY * LOOK_SENSITIVITY, -PITCH_LIMIT, PITCH_LIMIT);
    });
    window.addEventListener('keydown', (e) => this.keys.add(e.code));
    window.addEventListener('keyup', (e) => this.keys.delete(e.code));
    window.addEventListener('blur', () => this.keys.clear());
  }

  lookAt(target) {
    const d = new THREE.Vector3(...target).sub(this.pos);
    this.yaw = Math.atan2(-d.x, -d.z);
    this.pitch = Math.atan2(d.y, Math.hypot(d.x, d.z));
  }

  setView(name) {
    if (name === 'fly') {
      this.pos.set(this.pos.x, 180, this.pos.z + 300);
      this.mode = 'fly';
      this.lookAt(this.meta.anchors.opera_house);
      return;
    }
    const view = this.meta.views[name];
    this.pos.set(...view.pos);
    this.mode = 'walk';
    this.lookAt(view.look);
  }

  insideWalkZone(x, z) {
    return insidePolygon(this.meta.walkZone, x, z) && !this.meta.walkHoles.some((h) => insidePolygon(h, x, z));
  }

  /** Bilinear lookup in the walk-zone height grid exported by build_blockout.py */
  groundHeight(x, z) {
    const g = this.meta.ground;
    const fx = THREE.MathUtils.clamp((x - g.x0) / g.step, 0, g.nx - 1.001);
    const fz = THREE.MathUtils.clamp((z - g.z0) / g.step, 0, g.nz - 1.001);
    const ix = Math.floor(fx);
    const iz = Math.floor(fz);
    const tx = fx - ix;
    const tz = fz - iz;
    const h = (i, k) => g.h[(iz + k) * g.nx + ix + i];
    return (h(0, 0) * (1 - tx) + h(1, 0) * tx) * (1 - tz) + (h(0, 1) * (1 - tx) + h(1, 1) * tx) * tz;
  }

  canStep(x, z, nx, nz) {
    if (!this.insideWalkZone(nx, nz)) return false;
    const run = Math.hypot(nx - x, nz - z);
    return run === 0 || Math.abs(this.groundHeight(nx, nz) - this.groundHeight(x, z)) / run <= MAX_SLOPE;
  }

  update(dt) {
    const k = this.keys;
    const forward = new THREE.Vector3(-Math.sin(this.yaw), 0, -Math.cos(this.yaw));
    const right = new THREE.Vector3(-forward.z, 0, forward.x);
    const move = new THREE.Vector3();
    if (k.has('KeyW')) move.add(forward);
    if (k.has('KeyS')) move.sub(forward);
    if (k.has('KeyD')) move.add(right);
    if (k.has('KeyA')) move.sub(right);

    if (this.mode === 'fly') {
      if (k.has('KeyE')) move.y += 1;
      if (k.has('KeyQ')) move.y -= 1;
      this.pos.addScaledVector(move.normalize(), FLY_SPEED * (k.has('ShiftLeft') ? 4 : 1) * dt);
      this.pos.y = Math.max(this.pos.y, FLY_FLOOR);
      return;
    }
    if (move.lengthSq() > 0) {
      const step = move.normalize().multiplyScalar(WALK_SPEED * (k.has('ShiftLeft') ? RUN_MULTIPLIER : 1) * dt);
      const { x, z } = this.pos;
      // Slide along edges and steep ground instead of stopping dead
      if (this.canStep(x, z, x + step.x, z + step.z)) this.pos.set(x + step.x, this.pos.y, z + step.z);
      else if (this.canStep(x, z, x + step.x, z)) this.pos.x += step.x;
      else if (this.canStep(x, z, x, z + step.z)) this.pos.z += step.z;
    }
    this.pos.y = this.groundHeight(this.pos.x, this.pos.z) + this.meta.eyeHeight;
  }

  applyTo(camera) {
    camera.position.copy(this.pos);
    camera.rotation.set(this.pitch, this.yaw, 0, 'YXZ');
  }
}
