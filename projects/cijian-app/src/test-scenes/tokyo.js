// 东京测试场景：一条程序生成的小街，代替还没接进来的烘焙场景。不是正式美术。
// 打卡点用占位几何摆好，组的名字就是 Blender 里要放的点位名（ANCHOR_photo_xxx），拍照模块按名字找。
// 布局：主街沿 z 轴，−z 端是台阶（夕焼けだんだん，站在台阶顶朝 +z 看夕阳，和 game.js 的太阳方向一致），
// +z 端拼了浅草寺意象（大提灯的门、五重塔）。店名全部虚构。
import * as THREE from 'three';
import { makeSky, signTexture, stripeTexture, mulberry32 } from './sky.js';

const STEP_TOP = -36;   // 台阶顶边 z
const STEP_N = 12;
const STEP_D = 0.42;
const STEP_H = 2.6;     // 台阶总高

export function buildTokyo({ renderer, scene, sun, hemi }) {
  const sky = makeSky(renderer, scene, 500);
  const rand = mulberry32(7);
  const std = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.9, ...o });
  const add = (mesh, parent = scene, shadow = true) => {
    mesh.castShadow = mesh.receiveShadow = shadow;
    parent.add(mesh);
    return mesh;
  };

  const ground = add(new THREE.Mesh(new THREE.PlaneGeometry(400, 400), std(0x5d5a55, { roughness: 0.95 })));
  ground.rotation.x = -Math.PI / 2;
  ground.castShadow = false;
  const road = add(new THREE.Mesh(new THREE.PlaneGeometry(5, 64), std(0x8a8278, { roughness: 0.85 })));
  road.rotation.x = -Math.PI / 2;
  road.position.set(0, 0.01, 0);
  road.castShadow = false;

  // ---- 三家打卡的店（遥的店、喫茶 ひより、八百政），其他房子随机 ----
  const SHOPS = [
    { id: 'haruka', side: -1, z: -12, sign: '古道具・レコード 遥', signOpts: { bg: '#2b2723', fg: '#efe4cc' }, awning: 0x3d4a5c, extra: harukaExtras },
    { id: 'hiyori', side: 1, z: 2, sign: '喫茶 ひより', signOpts: { bg: '#f1e6cc', fg: '#5a3520' }, awning: 0x2f4a3a, extra: hiyoriExtras },
    { id: 'yaomasa', side: -1, z: 14, sign: '八百政', signOpts: { bg: '#3a2a1c', fg: '#f3ead6' }, stripes: ['#c23a2c', '#f3ead6'], extra: yaomasaExtras },
  ];
  const nearShop = (side, z0, z1) => SHOPS.some((s) => s.side === side && s.z > z0 - 2.6 && s.z < z1 + 2.6);

  const wallColors = [0xd9cbb3, 0xb9a68a, 0x8d7b67, 0xe8e0d0, 0x6f5f52, 0xc7b8a0];
  const norenColors = [0x23395b, 0x7a2a1f, 0x2f4a3a, 0x3a2f45];
  for (const side of [-1, 1]) {
    let z = -30;
    while (z < 30) {
      const w = 4 + rand() * 3;
      const h = 5 + rand() * 4;
      const d = 6;
      const house = add(new THREE.Mesh(new THREE.BoxGeometry(d, h, w), std(wallColors[Math.floor(rand() * wallColors.length)])));
      house.position.set(side * (3.5 + d / 2), h / 2, z + w / 2);
      const roof = add(new THREE.Mesh(new THREE.BoxGeometry(d + 0.6, 0.25, w + 0.3), std(0x3b3a3c, { roughness: 0.7 })));
      roof.position.set(house.position.x, h + 0.12, house.position.z);
      const front = side * 3.5;
      if (!nearShop(side, z, z + w)) {
        const door = add(new THREE.Mesh(new THREE.PlaneGeometry(w * 0.7, 2.4), std(0x241c16, { roughness: 0.4, emissive: 0x3a2410, emissiveIntensity: 0.6 })), scene, false);
        door.position.set(front - side * 0.01, 1.2, z + w / 2);
        door.rotation.y = -side * Math.PI / 2;
        const noren = add(new THREE.Mesh(new THREE.PlaneGeometry(w * 0.6, 0.9), std(norenColors[Math.floor(rand() * norenColors.length)], { side: THREE.DoubleSide, roughness: 1 })));
        noren.position.set(front - side * 0.06, 2.05, z + w / 2);
        noren.rotation.y = -side * Math.PI / 2;
        if (rand() > 0.5) {
          const lantern = add(new THREE.Mesh(new THREE.SphereGeometry(0.28, 16, 12), std(0xd8432c, { emissive: 0xff6a3a, emissiveIntensity: 1.4 })), scene, false);
          lantern.scale.y = 1.35;
          lantern.position.set(front - side * 0.9, 2.3, z + 0.6);
        }
      }
      z += w + 0.15;
    }
  }

  for (const s of SHOPS) {
    const g = new THREE.Group();
    g.name = `ANCHOR_photo_${s.id}`;
    g.position.set(s.side * 3.5, 0, s.z);
    g.rotation.y = s.side < 0 ? Math.PI / 2 : -Math.PI / 2; // 组的 +z 朝向街道
    const W = 4.6;
    add(new THREE.Mesh(new THREE.BoxGeometry(W, 3.4, 0.1), std(0x5a4632)), g).position.set(0, 1.7, 0.05);
    const glass = add(new THREE.Mesh(new THREE.PlaneGeometry(W * 0.62, 2.1), std(0x2a1d12, { roughness: 0.2, emissive: 0xffb36b, emissiveIntensity: 0.55 })), g, false);
    glass.position.set(0, 1.1, 0.11);
    const signMat = new THREE.MeshStandardMaterial({ map: signTexture(s.sign, { w: 768, h: 140, ...s.signOpts }), roughness: 0.8 });
    add(new THREE.Mesh(new THREE.BoxGeometry(W * 0.86, 0.62, 0.06), [std(0x2b2723), std(0x2b2723), std(0x2b2723), std(0x2b2723), signMat, std(0x2b2723)]), g).position.set(0, 3.0, 0.16);
    const awningMat = s.stripes
      ? new THREE.MeshStandardMaterial({ map: stripeTexture(...s.stripes, 12), roughness: 0.9 })
      : std(s.awning);
    const awning = add(new THREE.Mesh(new THREE.BoxGeometry(W, 0.05, 1.2), awningMat), g);
    awning.position.set(0, 2.5, 0.65);
    awning.rotation.x = 0.32;
    s.extra(g, { add, std });
    scene.add(g);
  }

  // ---- 电线杆：西段三根加电线是打卡点「电线杆与天空」----
  const poles = new THREE.Group();
  poles.name = 'ANCHOR_photo_poles';
  scene.add(poles);
  const poleMat = std(0x8f8a83);
  const wireMat = new THREE.MeshBasicMaterial({ color: 0x1b1a19 });
  const tops = [];
  for (let z = -28; z <= 28; z += 7) {
    const inGroup = z >= -28 && z <= -14;
    const parent = inGroup ? poles : scene;
    const pole = add(new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.15, 8.5, 10), poleMat), parent);
    pole.position.set(2.8, 4.25, z);
    for (const y of [7.6, 7.0]) {
      const arm = add(new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.08, 0.08), poleMat), parent);
      arm.position.set(2.8, y, z);
    }
    const tr = add(new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.6, 12), std(0x6f6d68)), parent);
    tr.position.set(3.15, 6.3, z);
    tops.push({ z, parent });
  }
  for (let i = 0; i < tops.length - 1; i++) {
    const a = tops[i];
    const b = tops[i + 1];
    const parent = a.parent === poles && b.parent === poles ? poles : scene;
    for (const [dx, y] of [[-0.6, 7.6], [0.6, 7.6], [-0.5, 7.0], [0.5, 7.0]]) {
      parent.add(wire(new THREE.Vector3(2.8 + dx, y, a.z), new THREE.Vector3(2.8 + dx, y, b.z), 0.35, wireMat));
    }
  }
  // 横过街的线，接到对面房子
  for (const z of [-28, -21, -14, 0, 14]) {
    const parent = z <= -14 ? poles : scene;
    parent.add(wire(new THREE.Vector3(2.8, 7.0, z), new THREE.Vector3(-3.6, 5.6, z + 1.5), 0.4, wireMat));
  }

  // ---- 街尾的台阶：夕焼けだんだん ----
  const platform = add(new THREE.Mesh(new THREE.BoxGeometry(14, STEP_H, 16), std(0x7d776e)));
  platform.position.set(0, STEP_H / 2, STEP_TOP - 8);
  for (const sx of [-1, 1]) {
    const wall = add(new THREE.Mesh(new THREE.BoxGeometry(0.5, STEP_H + 0.7, 5.6), std(0x8a8378)));
    wall.position.set(sx * 2.75, (STEP_H + 0.7) / 2, STEP_TOP + 2.6);
  }
  const steps = new THREE.Group();
  steps.name = 'ANCHOR_photo_dandan';
  scene.add(steps);
  for (let i = 0; i < STEP_N; i++) {
    const h = (STEP_H * (STEP_N - i)) / STEP_N;
    const step = add(new THREE.Mesh(new THREE.BoxGeometry(5, h, STEP_D), std(0x9d968b)), steps);
    step.position.set(0, h / 2, STEP_TOP + (i + 0.5) * STEP_D);
  }
  const rail = add(new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, Math.hypot(STEP_N * STEP_D, STEP_H), 8), std(0x4a4846, { metalness: 0.6, roughness: 0.4 })), steps);
  rail.position.set(0, STEP_H / 2 + 0.85, STEP_TOP + (STEP_N * STEP_D) / 2);
  rail.rotation.x = Math.atan2(STEP_N * STEP_D, STEP_H);
  // 台阶顶两侧几间房子做背景
  for (const sx of [-1, 1]) {
    const hb = add(new THREE.Mesh(new THREE.BoxGeometry(6, 6, 10), std(sx < 0 ? 0xb9a68a : 0x8d7b67)));
    hb.position.set(sx * 9, STEP_H + 3, STEP_TOP - 7);
  }

  // ---- 浅草寺意象：门和大提灯、五重塔（虚构比例，灯面不写字）----
  const gate = new THREE.Group();
  scene.add(gate);
  const red = std(0xa8281e, { roughness: 0.75 });
  for (const sx of [-1, 1]) add(new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.38, 6.4, 16), red), gate).position.set(sx * 3.4, 3.2, 40);
  add(new THREE.Mesh(new THREE.BoxGeometry(8.4, 0.5, 1.2), red), gate).position.set(0, 6.0, 40);
  add(new THREE.Mesh(new THREE.BoxGeometry(11, 0.6, 4.4), std(0x2e2c2c, { roughness: 0.6 })), gate).position.set(0, 6.6, 40);
  add(new THREE.Mesh(new THREE.BoxGeometry(9.6, 0.9, 3.2), std(0x2e2c2c, { roughness: 0.6 })), gate).position.set(0, 7.3, 40);
  const lantern = new THREE.Group();
  lantern.name = 'ANCHOR_photo_kaminarimon';
  lantern.position.set(0, 3.7, 40);
  scene.add(lantern);
  const prof = [];
  for (let i = 0; i <= 20; i++) {
    const y = -1.9 + (i / 20) * 3.8;
    prof.push(new THREE.Vector2(Math.max(1.05, 1.65 * Math.sqrt(Math.max(0, 1 - (y / 2.05) ** 2))), y));
  }
  add(new THREE.Mesh(new THREE.LatheGeometry(prof, 40), std(0xb3261e, { roughness: 0.8, emissive: 0x5a0d06, emissiveIntensity: 0.25, side: THREE.DoubleSide })), lantern);
  for (const y of [-2.0, 2.0]) add(new THREE.Mesh(new THREE.CylinderGeometry(1.12, 1.12, 0.32, 40), std(0x1d1a17, { roughness: 0.5, metalness: 0.3 })), lantern).position.y = y;
  for (const y of [-1.2, -0.4, 0.4, 1.2]) {
    const r = 1.65 * Math.sqrt(1 - (y / 2.05) ** 2) + 0.01;
    const ring = add(new THREE.Mesh(new THREE.TorusGeometry(r, 0.02, 6, 48), std(0x5a120c)), lantern, false);
    ring.rotation.x = Math.PI / 2;
    ring.position.y = y;
  }
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.6, 6), std(0x1d1a17)), lantern).position.y = 2.4;

  const pagoda = new THREE.Group();
  pagoda.name = 'ANCHOR_photo_pagoda';
  pagoda.position.set(16, 0, 62);
  scene.add(pagoda);
  add(new THREE.Mesh(new THREE.BoxGeometry(10, 1.5, 10), std(0x8a8378)), pagoda).position.y = 0.75;
  let y = 1.5;
  for (let i = 0; i < 5; i++) {
    const w = 6.6 - i * 0.7;
    add(new THREE.Mesh(new THREE.BoxGeometry(w, 3.0, w), std(0xb0382a, { roughness: 0.8 })), pagoda).position.y = y + 1.5;
    y += 3.0;
    const roof = add(new THREE.Mesh(new THREE.ConeGeometry(w * 0.98, 1.3, 4, 1, true), std(0x2e2c2c, { roughness: 0.6, side: THREE.DoubleSide })), pagoda);
    roof.rotation.y = Math.PI / 4;
    roof.position.y = y + 0.4;
    y += 0.9;
  }
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.2, 7.5, 8), std(0x9a8a5a, { metalness: 0.7, roughness: 0.4 })), pagoda).position.y = y + 3.7;
  for (let k = 0; k < 6; k++) {
    const ring = add(new THREE.Mesh(new THREE.TorusGeometry(0.5 - k * 0.03, 0.05, 6, 20), std(0x9a8a5a, { metalness: 0.7, roughness: 0.4 })), pagoda);
    ring.position.set(0, y + 1.5 + k * 0.9, 0);
    ring.rotation.x = Math.PI / 2;
  }

  // ---- 时段 ----
  const SUNSET_DIR = new THREE.Vector3(0.035, 0.107, 0.999).normalize(); // 和 presets/tokyo.js 一致，仰角约 6°
  const PH = {
    day: { dir: new THREE.Vector3(0.45, 0.8, 0.3).normalize(), sun: 0xfff4e0, sunI: 4.0, hemiI: 1.1, sky: { top: 0x3f78bf, horizon: 0xc4d8ea, bottom: 0x8a8a86, sunColor: 0xfff0d8, glow: 0.6 }, fog: 0xbcd3ea },
    sunset: { dir: SUNSET_DIR, sun: 0xffa45c, sunI: 7.5, hemiI: 0.45, sky: { top: 0x2f4370, horizon: 0xf09a5a, bottom: 0x4a3a34, sunColor: 0xffa860, glow: 1.4, sunSize: 0.03 }, fog: 0xd99573 },
  };
  function setPhase(key) {
    const p = PH[key];
    sun.color.set(p.sun);
    sun.intensity = p.sunI;
    hemi.intensity = p.hemiI;
    sun.target.position.set(0, 0, 0);
    sun.position.copy(p.dir).multiplyScalar(90);
    Object.assign(sun.shadow.camera, { left: -55, right: 55, top: 55, bottom: -55, near: 1, far: 220 });
    sun.shadow.camera.updateProjectionMatrix();
    sky.set({ ...p.sky, sunDir: p.dir.toArray() });
    scene.fog = new THREE.Fog(p.fog, 40, 260);
  }

  return {
    far: 600,
    eye: 1.6,
    spawn: { pos: [0, 0, 22], yaw: 0 },
    setPhase,
    heightAt(x, z) {
      if (z <= STEP_TOP && Math.abs(x) < 7) return STEP_H;
      if (z > STEP_TOP && z < STEP_TOP + STEP_N * STEP_D && Math.abs(x) < 2.5) {
        const i = Math.floor((z - STEP_TOP) / STEP_D);
        return (STEP_H * (STEP_N - i)) / STEP_N;
      }
      return 0;
    },
    // 每个打卡点一个参考机位，测试页的“去这里”按钮用：[x, z] 站位，看向 at，附带建议的焦段、横竖、低角度、时段
    viewpoints: {
      tk_haruka: { pos: [2.0, -8.0], at: [-3.4, 1.7, -12], focal: 35 },
      tk_hiyori: { pos: [-2.0, 6.0], at: [3.4, 1.8, 2], focal: 35 },
      tk_yaomasa: { pos: [2.0, 18.0], at: [-3.4, 1.5, 14], focal: 35 },
      tk_dandan: { pos: [0, -37.4], at: [0, 1.2, -24], focal: 24, phase: 'sunset', ev: 2 / 3 },
      tk_kaminarimon: { pos: [0.3, 31.0], at: [0, 4.2, 40], focal: 35, portrait: true, low: true },
      tk_pagoda: { pos: [9, 38], at: [16, 15, 62], focal: 24, portrait: true, low: true },
      tk_poles: { pos: [0.6, -24.5], at: [2.8, 7.6, -19], focal: 24, portrait: true },
    },
  };
}

function wire(a, b, sag, mat) {
  const mid = a.clone().lerp(b, 0.5);
  mid.y -= sag;
  const curve = new THREE.CatmullRomCurve3([a, a.clone().lerp(mid, 0.55).setY(mid.y + sag * 0.3), mid, b.clone().lerp(mid, 0.55).setY(mid.y + sag * 0.3), b]);
  return new THREE.Mesh(new THREE.TubeGeometry(curve, 24, 0.018, 4), mat);
}

// 遥的店：门口的风铃、店外两箱唱片
function harukaExtras(g, { add, std }) {
  const bell = new THREE.Group();
  bell.position.set(1.4, 2.25, 0.75);
  g.add(bell);
  add(new THREE.Mesh(new THREE.SphereGeometry(0.11, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2), std(0xdfeff2, { roughness: 0.1, transparent: true, opacity: 0.8, side: THREE.DoubleSide })), bell, false);
  add(new THREE.Mesh(new THREE.PlaneGeometry(0.08, 0.3), std(0xc23a2c, { side: THREE.DoubleSide })), bell, false).position.y = -0.3;
  for (const x of [-1.5, -0.6]) {
    const crate = add(new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.4, 0.45), std(0x7a5a3a)), g);
    crate.position.set(x, 0.55, 0.6);
    for (let k = 0; k < 6; k++) {
      const rec = add(new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.32, 0.01), std([0x1d1a17, 0xd9cbb3, 0x7a2a1f, 0x23395b][k % 4])), g, false);
      rec.position.set(x, 0.85, 0.42 + k * 0.06);
      rec.rotation.x = -0.25;
    }
    add(new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.35, 0.06), std(0x3a2a1c)), g).position.set(x, 0.17, 0.6);
  }
}

// 喫茶：门口的立式菜单板和一盆植物
function hiyoriExtras(g, { add, std }) {
  const board = add(new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.9, 0.05), [std(0x3a2a1c), std(0x3a2a1c), std(0x3a2a1c), std(0x3a2a1c), new THREE.MeshStandardMaterial({ map: signTexture('珈琲 ・ 本日のケーキ', { w: 160, h: 256, bg: '#22302a', fg: '#efe4cc', vertical: true }), roughness: 0.9 }), std(0x3a2a1c)]), g);
  board.position.set(1.5, 0.6, 0.9);
  board.rotation.x = -0.12;
  const pot = add(new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.17, 0.4, 14), std(0x9a5a3a)), g);
  pot.position.set(-1.7, 0.2, 0.45);
  add(new THREE.Mesh(new THREE.SphereGeometry(0.42, 12, 10), std(0x3f6a3a)), g).position.set(-1.7, 0.75, 0.45);
}

// 八百政：门口一排菜筐
function yaomasaExtras(g, { add, std }) {
  const colors = [0xc8321e, 0xe08a2a, 0x6a9a3a, 0xe9d24a, 0x8a3a6a];
  const shelf = add(new THREE.Mesh(new THREE.BoxGeometry(3.8, 0.7, 1.0), std(0x7a5a3a)), g);
  shelf.position.set(0, 0.35, 0.75);
  shelf.rotation.x = 0.0;
  const r = mulberry32(3);
  for (let i = 0; i < 5; i++) {
    const x = -1.5 + i * 0.75;
    add(new THREE.Mesh(new THREE.BoxGeometry(0.66, 0.16, 0.8), std(0x9a7a52)), g).position.set(x, 0.78, 0.75);
    for (let k = 0; k < 9; k++) {
      const v = add(new THREE.Mesh(new THREE.SphereGeometry(0.09 + r() * 0.03, 10, 8), std(colors[i], { roughness: 0.55 })), g, false);
      v.position.set(x + (r() - 0.5) * 0.5, 0.92 + r() * 0.06, 0.5 + r() * 0.5);
    }
  }
  for (let k = 0; k < 4; k++) {
    const dk = add(new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.03, 0.7, 8), std(0xf1ece0, { roughness: 0.6 })), g, false);
    dk.position.set(1.9, 0.75 + k * 0.03, 0.55 + k * 0.12);
    dk.rotation.z = Math.PI / 2 - 0.3;
  }
}
