import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// Trees from web/data/trees.json (OSM natural=tree plus scatter in mapped bush).
// Crowns are clusters of alpha-tested leaf cards (a common real-time foliage technique): each card
// carries a painted sprig of leaves, and its normals point away from the crown centre so the crown
// shades as a soft volume. Trees are split into spatial chunks so the camera and each shadow
// cascade only draw the chunks they can see.

const CHUNK = 700;      // metres per tree chunk: few enough draw calls, still culled per cascade
const BARK = new THREE.Color(0x4a3c31);
const PALE_BARK = new THREE.Color(0xb0a490);

function seeded(seed) {
  let s = seed;
  return () => ((s = (s * 16807) % 2147483647) / 2147483647);
}

/** Leaf sprite drawn once on a canvas: many small leaves in mixed greens on transparency. */
function leafTexture() {
  const size = 256;
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext('2d');
  const rand = seeded(11);
  // Dense enough (~80 % of the disc covered) that the coarse mip levels stay above the alpha
  // threshold; otherwise distant crowns dissolve and leave bare trunks
  for (let i = 0; i < 900; i++) {
    const a = rand() * Math.PI * 2;
    const r = Math.sqrt(rand()) * size * 0.45;
    const x = size / 2 + Math.cos(a) * r;
    const y = size / 2 + Math.sin(a) * r;
    const g = 95 + rand() * 105;
    ctx.fillStyle = `rgb(${Math.round(g * 0.62)},${Math.round(g)},${Math.round(g * 0.42)})`;
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rand() * Math.PI * 2);
    ctx.beginPath();
    ctx.ellipse(0, 0, 5 + rand() * 7, 2.5 + rand() * 3.5, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

function colorize(geometry, color) {
  const g = geometry.index ? geometry.toNonIndexed() : geometry;
  const n = g.getAttribute('position').count;
  const colors = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) colors.set([color.r, color.g, color.b], i * 3);
  g.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  return g;
}

function trunk(bottomR, topR, height, color) {
  const g = new THREE.CylinderGeometry(topR, bottomR, height, 5, 1, true);
  g.translate(0, height / 2, 0);
  return colorize(g, color);
}

/**
 * `count` leaf cards scattered through an ellipsoid crown. Cards are tinted darker towards the
 * bottom and the inside of the crown, and their normals point outward from the crown centre.
 */
function crown(count, radii, centre, cardSize, color, rand) {
  const cards = [];
  const c = new THREE.Vector3(...centre);
  for (let i = 0; i < count; i++) {
    const dir = new THREE.Vector3(rand() * 2 - 1, rand() * 2 - 1, rand() * 2 - 1).normalize();
    const depth = 0.35 + 0.65 * Math.cbrt(rand());
    const p = new THREE.Vector3(dir.x * radii[0], dir.y * radii[1], dir.z * radii[2]).multiplyScalar(depth).add(c);
    const card = new THREE.PlaneGeometry(cardSize, cardSize);
    card.rotateX(rand() * Math.PI);
    card.rotateY(rand() * Math.PI * 2);
    card.translate(p.x, p.y, p.z);
    const pos = card.getAttribute('position');
    const nor = card.getAttribute('normal');
    const col = new Float32Array(pos.count * 3);
    const shade = (0.55 + 0.45 * depth) * (0.7 + 0.3 * THREE.MathUtils.clamp((p.y - c.y) / radii[1] + 0.5, 0, 1));
    for (let v = 0; v < pos.count; v++) {
      const out = new THREE.Vector3(pos.getX(v), pos.getY(v), pos.getZ(v)).sub(c);
      out.y *= 0.6;
      out.normalize();
      nor.setXYZ(v, out.x, out.y, out.z);
      col.set([color.r * shade, color.g * shade, color.b * shade], v * 3);
    }
    card.setAttribute('color', new THREE.BufferAttribute(col, 3));
    cards.push(card.toNonIndexed());
  }
  return cards;
}

function buildKinds() {
  const rand = seeded(42);
  // [trunk, leaf cards]; every model is 1 m tall and scaled per instance to the tree's height
  const kinds = [
    [trunk(0.04, 0.025, 0.55, BARK),            // street and park broadleaves
      crown(26, [0.36, 0.28, 0.36], [0, 0.66, 0], 0.32, new THREE.Color(0x5d7a3a), rand)],
    [trunk(0.09, 0.05, 0.42, BARK),             // Moreton Bay fig: broad, low, very dark
      crown(34, [0.6, 0.24, 0.6], [0, 0.6, 0], 0.36, new THREE.Color(0x3c5a2c), rand)],
    [trunk(0.03, 0.018, 0.8, PALE_BARK),        // eucalypt: open grey-green crown on a pale trunk
      crown(18, [0.24, 0.2, 0.24], [0.03, 0.8, 0], 0.22, new THREE.Color(0x7a8662), rand)],
    [trunk(0.028, 0.024, 0.92, BARK),           // palm
      crown(12, [0.26, 0.08, 0.26], [0, 0.95, 0], 0.3, new THREE.Color(0x587a34), rand)],
  ];
  return kinds.map(([wood, leaves]) => ({ wood, leaves: mergeGeometries(leaves) }));
}

export async function createTrees(csm) {
  const data = await (await fetch('./data/trees.json')).json();
  const kinds = buildKinds();
  const leafMaterial = new THREE.MeshStandardMaterial({
    map: leafTexture(), vertexColors: true, alphaTest: 0.4, side: THREE.DoubleSide, roughness: 0.85,
    alphaToCoverage: true, // soft leaf edges with the composer's 4x MSAA target
  });
  const woodMaterial = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95 });
  csm.setupMaterial(leafMaterial);
  csm.setupMaterial(woodMaterial);

  // "chunkX,chunkZ,kind" -> trees
  const chunks = new Map();
  for (const t of data.trees) {
    const key = `${Math.floor(t[0] / CHUNK)},${Math.floor(t[2] / CHUNK)},${t[4]}`;
    if (!chunks.has(key)) chunks.set(key, []);
    chunks.get(key).push(t);
  }

  const group = new THREE.Group();
  group.name = 'Trees';
  const rand = seeded(7);
  const m = new THREE.Matrix4();
  const q = new THREE.Quaternion();
  const tint = new THREE.Color();
  const up = new THREE.Vector3(0, 1, 0);
  for (const [key, list] of chunks) {
    const kind = kinds[Number(key.split(',')[2])];
    const wood = new THREE.InstancedMesh(kind.wood, woodMaterial, list.length);
    const leaves = new THREE.InstancedMesh(kind.leaves, leafMaterial, list.length);
    list.forEach(([x, y, z, height], i) => {
      const spread = 0.8 + 0.45 * rand();
      q.setFromAxisAngle(up, rand() * Math.PI * 2);
      m.compose(new THREE.Vector3(x, y - 0.3, z), q, new THREE.Vector3(height * spread, height, height * spread));
      wood.setMatrixAt(i, m);
      leaves.setMatrixAt(i, m);
      leaves.setColorAt(i, tint.setHSL(0.24 + 0.06 * rand(), 0.25, 0.42 + 0.12 * rand()).multiplyScalar(2.1));
    });
    for (const mesh of [wood, leaves]) {
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.computeBoundingSphere();
      group.add(mesh);
    }
  }
  return { group, count: data.trees.length, chunks: chunks.size };
}
