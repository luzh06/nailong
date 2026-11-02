// 悉尼测试场景：北岸步道远眺海港，代替 sydney-harbour 的正式场景。不是正式美术。
// 坐标和正式场景一致：原点在歌剧院，x 东、y 上、−z 北，单位米；距离按真实大致比例
// （北岸步道到歌剧院约 1 公里、到大桥约 500 米），这样焦段和打卡判定的测试才有意义。
// 打卡点组的名字就是点位名（ANCHOR_photo_xxx）。咖啡店、长椅、地标是虚构的占位。
import * as THREE from 'three';
import { makePerson } from './people.js';
import { makeSky, signTexture, stripeTexture, mulberry32 } from './sky.js';

const SHORE_Z = -975;   // 北岸岸线
const LAND_Y = 2;       // 步道高出水面

export function buildSydney({ renderer, scene, sun, hemi }) {
  const sky = makeSky(renderer, scene, 5200);
  const rand = mulberry32(11);
  const std = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.85, ...o });
  const add = (mesh, parent = scene, shadow = true) => {
    mesh.castShadow = mesh.receiveShadow = shadow;
    parent.add(mesh);
    return mesh;
  };
  const box = (w, h, d, mat, x, y, z, parent = scene, shadow = true) => {
    const m = add(new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat), parent, shadow);
    m.position.set(x, y, z);
    return m;
  };

  // ---- 水和陆地 ----
  const water = add(new THREE.Mesh(new THREE.PlaneGeometry(12000, 12000), std(0x16303e, { roughness: 0.07, metalness: 0 })), scene, false);
  water.rotation.x = -Math.PI / 2;
  water.receiveShadow = true;
  const grass = std(0x55663f, { roughness: 0.95 });
  box(3600, LAND_Y, 2000, grass, -250, LAND_Y / 2, SHORE_Z - 1000, scene, false).receiveShadow = true;
  box(400, 0.05, 14, std(0xb9ae9c, { roughness: 0.9 }), -300, LAND_Y + 0.02, SHORE_Z - 7, scene, false).receiveShadow = true; // 步道铺装
  box(3600, LAND_Y, 2600, std(0x6a6a5e), -250, LAND_Y / 2, 1450, scene, false); // 南岸（城区）
  box(220, LAND_Y, 220, std(0x9a9284), 0, LAND_Y / 2, 40, scene, false);         // 歌剧院所在的岬角
  // 海堤和栏杆
  box(400, LAND_Y + 0.4, 0.8, std(0x9b9182), -300, (LAND_Y + 0.4) / 2 - 0.2, SHORE_Z - 0.4);
  const railMat = std(0x3a3d40, { metalness: 0.6, roughness: 0.4 });
  for (let x = -400; x <= -200; x += 2.5) box(0.06, 1.0, 0.06, railMat, x, LAND_Y + 0.7, SHORE_Z - 1.2, scene, false);
  box(200, 0.06, 0.08, railMat, -300, LAND_Y + 1.2, SHORE_Z - 1.2, scene, false);
  // 几棵树（无花果树的意思）
  for (const [x, z, s] of [[-350, -995, 1.2], [-312, -1004, 1.0], [-245, -996, 1.3], [-225, -1010, 1.1], [-372, -1012, 1.4]]) {
    box(0.5, 3 * s, 0.5, std(0x5a4a3a), x, LAND_Y + 1.5 * s, z);
    const crown = add(new THREE.Mesh(new THREE.SphereGeometry(3.2 * s, 14, 10), std(0x3d5a32, { roughness: 1 })));
    crown.position.set(x, LAND_Y + 4.6 * s, z);
    crown.scale.y = 0.75;
  }

  // ---- S1 Maya 的咖啡店：店面加露台上一桌朋友（组 = 露台上的人和桌子）----
  const cafeX = -335;
  const cafeZ = SHORE_Z - 28;
  box(12, 4.2, 8, std(0xe6ddcc), cafeX, LAND_Y + 2.1, cafeZ - 4);
  box(9, 2.6, 0.05, std(0x2a1d12, { roughness: 0.2, emissive: 0xffc27a, emissiveIntensity: 0.5 }), cafeX, LAND_Y + 1.5, cafeZ + 0.02, scene, false);
  const signMat = new THREE.MeshStandardMaterial({ map: signTexture('Café Maya', { w: 640, h: 120, bg: '#f4ecdc', fg: '#2f4a3a', font: 'Georgia,serif', weight: 400 }), roughness: 0.8 });
  box(6, 0.7, 0.08, [std(0x2f4a3a), std(0x2f4a3a), std(0x2f4a3a), std(0x2f4a3a), signMat, std(0x2f4a3a)], cafeX, LAND_Y + 3.65, cafeZ + 0.06);
  const awning = box(12, 0.06, 2.4, new THREE.MeshStandardMaterial({ map: stripeTexture('#2f4a3a', '#f4ecdc', 14), roughness: 0.9 }), cafeX, LAND_Y + 2.9, cafeZ + 1.2);
  awning.rotation.x = 0.28;
  const group = new THREE.Group();
  group.name = 'ANCHOR_photo_cafe';
  group.position.set(cafeX, LAND_Y, cafeZ + 4.5);
  scene.add(group);
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.75, 0.75, 0.05, 24), std(0xf1ece0)), group).position.y = 0.75;
  add(new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.75, 8), railMat), group).position.y = 0.37;
  const shirt = [0xc65a3a, 0x3a5a8a, 0xe2c26a, 0x5a7a4a, 0x8a4a6a];
  for (let i = 0; i < 5; i++) {
    const a = (i / 5) * Math.PI * 2 + 0.6;
    const p = new THREE.Group();
    p.position.set(Math.cos(a) * 1.15, 0, Math.sin(a) * 1.15);
    if (i === 1) p.name = 'NPC_maya'; // 站着、面朝步道的这位是 Maya（合影要先问她）
    group.add(p);
    const sit = i % 2 === 0;
    add(new THREE.Mesh(new THREE.CapsuleGeometry(0.2, sit ? 0.45 : 0.75, 4, 10), std(shirt[i])), p).position.y = sit ? 0.85 : 1.05;
    add(new THREE.Mesh(new THREE.SphereGeometry(0.13, 12, 10), std(0xd9b08c)), p).position.y = sit ? 1.33 : 1.7;
    if (sit) add(new THREE.Mesh(new THREE.BoxGeometry(0.45, 0.45, 0.45), std(0x6a5a4a)), p).position.y = 0.22;
  }

  // Camille：刚到咖啡店门口（占位人形）
  const camille = makePerson({ name: 'NPC_camille', color: 0x8c3b44, hair: 0x6a4026, height: 1.66 });
  camille.position.set(cafeX + 3.4, LAND_Y, cafeZ + 6.2);
  camille.rotation.y = -0.5;
  scene.add(camille);
  const npcs = [camille];

  // ---- S2 步道地标：投币望远镜和一块说明牌 ----
  const mark = new THREE.Group();
  mark.name = 'ANCHOR_photo_landmark';
  mark.position.set(-292, LAND_Y, SHORE_Z - 4);
  scene.add(mark);
  const brass = std(0x6c6a3a, { metalness: 0.8, roughness: 0.35 });
  box(0.14, 1.05, 0.14, railMat, 0, 0.52, 0, mark);
  box(0.35, 0.05, 0.35, railMat, 0, 0.02, 0, mark);
  const scope = add(new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.16, 0.55, 14), brass), mark);
  scope.position.set(0, 1.2, 0);
  scope.rotation.x = Math.PI / 2 - 0.15;
  box(0.36, 0.22, 0.22, brass, 0, 1.2, -0.25, mark);
  const plaque = box(0.7, 0.45, 0.05, [railMat, railMat, railMat, railMat, new THREE.MeshStandardMaterial({ map: signTexture('LOOKOUT 07', { w: 256, h: 160, bg: '#2e3a34', fg: '#e9e2d0', font: 'Georgia,serif' }) }), railMat], 0.9, 0.95, 0, mark);
  plaque.rotation.x = -0.4;
  box(0.08, 0.8, 0.08, railMat, 0.9, 0.4, 0, mark);

  // ---- S3 Sam 的长椅：朝着海 ----
  const bench = new THREE.Group();
  bench.name = 'ANCHOR_photo_bench';
  bench.position.set(-262, LAND_Y, SHORE_Z - 5.5);
  scene.add(bench);
  const wood = std(0x8a6a4a);
  for (const z of [-0.12, 0.05, 0.22]) box(1.8, 0.05, 0.13, wood, 0, 0.45, z, bench);
  for (const y of [0.65, 0.82]) box(1.8, 0.12, 0.04, wood, 0, y, -0.25, bench).rotation.x = -0.15;
  for (const x of [-0.8, 0.8]) {
    box(0.06, 0.45, 0.5, railMat, x, 0.22, 0, bench);
    box(0.06, 0.5, 0.06, railMat, x, 0.7, -0.26, bench);
  }
  const plaq = box(0.18, 0.06, 0.01, brass, 0, 0.74, -0.22, bench, false);
  plaq.rotation.x = -0.15;

  // ---- S4 黄昏的海：只放一个空物体（模拟 Blender 里的 Empty），按点 + 半径算 ----
  const shore = new THREE.Object3D();
  shore.name = 'ANCHOR_photo_shore';
  shore.position.set(-700, 0, SHORE_Z + 60);
  scene.add(shore);

  // ---- S5 远景剧院：基座 + 两排帆形壳体（示意）----
  const opera = new THREE.Group();
  opera.name = 'ANCHOR_photo_opera';
  scene.add(opera);
  const podium = std(0xc9b49a, { roughness: 0.9 });
  box(110, 8, 180, podium, 0, LAND_Y + 4, 10, opera);
  const shellMat = std(0xf3efe6, { roughness: 0.35, side: THREE.DoubleSide });
  const shellGeo = new THREE.SphereGeometry(1, 28, 14, 0, Math.PI, 0, Math.PI / 2);
  const shells = [
    [-22, -60, 34, 40, 0.0], [-22, -32, 30, 52, 0.0], [-22, -2, 26, 62, 0.0], [-22, 28, 18, 38, Math.PI],
    [22, -48, 28, 34, 0.0], [22, -20, 26, 46, 0.0], [22, 8, 22, 54, 0.0], [22, 34, 16, 32, Math.PI],
  ];
  for (const [x, z, len, h, flip] of shells) {
    const m = add(new THREE.Mesh(shellGeo, shellMat), opera);
    m.scale.set(16, h, len);
    m.rotation.set(0, Math.PI / 2 + flip, 0);
    m.position.set(x, LAND_Y + 8, z);
  }

  // ---- S6 海港大桥：钢拱 + 桥面 + 四座桥塔（示意，跨度约 500 米、拱顶约 134 米）----
  const bridge = new THREE.Group();
  bridge.name = 'ANCHOR_photo_bridge';
  scene.add(bridge);
  const steel = std(0x5d6266, { metalness: 0.5, roughness: 0.6 });
  const BX = -760;
  const BZ0 = -920;
  const BZ1 = -420;
  const arch = (top, base, x) => {
    const pts = [];
    for (let i = 0; i <= 32; i++) {
      const t = i / 32;
      pts.push(new THREE.Vector3(x, base + (top - base) * 4 * t * (1 - t), BZ0 + (BZ1 - BZ0) * t));
    }
    return add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 64, 3, 6), steel), bridge);
  };
  for (const dx of [-14, 14]) {
    arch(134, 10, BX + dx);
    arch(118, 18, BX + dx);
    for (let i = 1; i < 16; i++) {
      const t = i / 16;
      const z = BZ0 + (BZ1 - BZ0) * t;
      const topY = 18 + (118 - 18) * 4 * t * (1 - t);
      if (topY > 52) box(1.2, topY - 49, 1.2, steel, BX + dx, (topY + 49) / 2, z, bridge, false);
    }
  }
  box(48, 4, 1100, steel, BX, 49, (BZ0 + BZ1) / 2, bridge);
  for (const z of [BZ0 - 20, BZ0 + 10, BZ1 - 10, BZ1 + 20]) {
    for (const dx of [-20, 20]) box(16, 89, 22, std(0xb1a48c), BX + dx, 44.5, z, bridge);
  }
  // 桥上的灯（蓝调时亮）
  const lampMat = new THREE.MeshStandardMaterial({ color: 0x222222, emissive: 0xffd9a0, emissiveIntensity: 0 });
  const lampGeo = new THREE.SphereGeometry(1.2, 6, 4);
  for (let i = 0; i <= 30; i++) {
    for (const dx of [-23, 23]) {
      const m = new THREE.Mesh(lampGeo, lampMat);
      m.position.set(BX + dx, 53, BZ0 - 80 + (i / 30) * 660);
      bridge.add(m);
    }
  }

  // ---- 城区（S7 蓝调时分的亮灯对象）----
  const cbd = new THREE.Group();
  cbd.name = 'ANCHOR_photo_bluehour';
  scene.add(cbd);
  const winTex = windowTexture(rand);
  const towerMats = [0x8c96a0, 0x6f7a84, 0xa8a49a, 0x5d6a74].map((c) =>
    new THREE.MeshStandardMaterial({ color: c, roughness: 0.45, metalness: 0.3, emissive: 0xffd7a0, emissiveMap: winTex, emissiveIntensity: 0 }),
  );
  for (let i = 0; i < 46; i++) {
    const x = -1150 + rand() * 1000;
    const z = 260 + rand() * 700;
    const w = 25 + rand() * 30;
    const h = 40 + rand() ** 1.6 * 200;
    box(w, h, w * (0.8 + rand() * 0.6), towerMats[i % 4], x, LAND_Y + h / 2, z, cbd, false);
  }

  // ---- 时段：南半球，正午太阳在北边（−z）；黄昏太阳落在西边（−x）----
  const PH = {
    day: { dir: [0.25, 0.85, -0.45], sun: 0xfff4e6, sunI: 3.4, hemiI: 1.0, hemiSky: 0xbcd3ff, sky: { top: 0x3a78c6, horizon: 0xcfe0ee, bottom: 0x24485a, sunColor: 0xfff0d8, glow: 0.5 }, fog: [0xc9d9e6, 900, 7000], lights: 0, opera: 0 },
    golden: { dir: [-0.97, 0.1, 0.2], sun: 0xffb070, sunI: 4.8, hemiI: 0.5, hemiSky: 0xffc9a0, sky: { top: 0x3e5280, horizon: 0xf4a66a, bottom: 0x3a3a48, sunColor: 0xffb070, glow: 1.6, sunSize: 0.025 }, fog: [0xe2ab84, 700, 6500], lights: 0.15, opera: 0 },
    blue: { dir: [-0.95, -0.06, 0.25], sun: 0x8090c0, sunI: 0, hemiI: 0.28, hemiSky: 0x5a78c0, sky: { top: 0x0d1a3a, horizon: 0x3f63a0, bottom: 0x0d1626, sunColor: 0x5a70b0, glow: 0.6, sunSize: 0.001 }, fog: [0x2c4068, 600, 6000], lights: 1.6, opera: 0.35 },
  };
  const operaMat = shellMat;
  function setPhase(key) {
    const p = PH[key];
    const dir = new THREE.Vector3(...p.dir).normalize();
    sun.color.set(p.sun);
    sun.intensity = p.sunI;
    hemi.intensity = p.hemiI;
    hemi.color.set(p.hemiSky);
    sun.target.position.set(-300, 0, SHORE_Z - 10);
    sun.position.copy(sun.target.position).addScaledVector(dir, 200);
    Object.assign(sun.shadow.camera, { left: -70, right: 70, top: 70, bottom: -70, near: 1, far: 500 });
    sun.shadow.camera.updateProjectionMatrix();
    sky.set({ ...p.sky, sunDir: p.dir });
    scene.fog = new THREE.Fog(...p.fog);
    towerMats.forEach((m) => (m.emissiveIntensity = p.lights));
    lampMat.emissiveIntensity = p.lights * 4;
    operaMat.emissive.set(0xffe2b8);
    operaMat.emissiveIntensity = p.opera;
  }

  return {
    far: 8000,
    eye: 1.6,
    npcs,
    spawn: { pos: [-300, SHORE_Z - 10], yaw: Math.PI },
    setPhase,
    heightAt: () => LAND_Y,
    clamp(pos) {
      pos.z = Math.min(pos.z, SHORE_Z - 1.6);
    },
    viewpoints: {
      sy_cafe: { pos: [-331, SHORE_Z - 15], at: [cafeX, LAND_Y + 1.1, cafeZ + 4.5], focal: 28 },
      sy_landmark: { pos: [-294.2, SHORE_Z - 10], at: [-289, LAND_Y + 1.0, SHORE_Z + 10], focal: 50 },
      sy_bench: { pos: [-266.5, SHORE_Z - 10.5], at: [-262, LAND_Y + 0.5, SHORE_Z - 5.5], focal: 50 },
      sy_shore: { pos: [-300, SHORE_Z - 3], at: [-700, 20, SHORE_Z + 60], focal: 28, phase: 'golden' },
      sy_opera: { pos: [-300, SHORE_Z - 3], at: [0, 30, 0], focal: 135 },
      sy_bridge: { pos: [-300, SHORE_Z - 3], at: [-760, 70, -670], focal: 50 },
      sy_bluehour: { pos: [-300, SHORE_Z - 3], at: [-560, 60, 560], focal: 50, phase: 'blue', ev: -1 / 3 },
    },
  };
}

// 写字楼窗户：随机亮着的格子
function windowTexture(rand) {
  const c = document.createElement('canvas');
  c.width = 64;
  c.height = 256;
  const g = c.getContext('2d');
  g.fillStyle = '#000';
  g.fillRect(0, 0, 64, 256);
  for (let y = 0; y < 64; y++) {
    for (let x = 0; x < 8; x++) {
      if (rand() < 0.45) {
        g.fillStyle = `rgb(${200 + rand() * 55},${170 + rand() * 60},${110 + rand() * 60})`;
        g.fillRect(x * 8 + 1, y * 4 + 1, 6, 2);
      }
    }
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
