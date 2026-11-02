// 各城拍照配置共用的部分：按点位名找打卡点、切时段、集纪念章、拼回忆卡文字。
// 每座城市自己的数据（打卡点、焦段、时段、回忆卡文字）在 tokyo.js / sydney.js 里，改那里就行。
import * as THREE from 'three';
import { drawStamp } from '../stamps.js';

const WEATHER = { clear: '晴', cloudy: '多云', rain: '小雨', drizzle: '小雨转晴' };

/**
 * 把一座城的打卡点定义变成 PhotoSystem 能用的 spots。
 * 按点位名（比如 ANCHOR_photo_haruka）在场景里找物体，或者在 anchors.json 里找坐标；找不到就跳过并在控制台提示。
 *
 * @param {object} city   TOKYO / SYDNEY
 * @param {THREE.Object3D|object} source  场景（或场景里的一个组），或者读进来的 anchors.json
 * @param {object} [o]
 * @param {'three'|'blender'} [o.coords]  anchors.json 里坐标是哪个坐标系；blender 会换成 three：(x, y, z) → (x, z, −y)
 * @param {object} [o.overrides]  按打卡点 id 改个别字段，比如 { tk_dandan: { minCoverage: 0.05 } }
 * @param {(def) => boolean} [o.include]  只要一部分，比如 (d) => d.required
 * @param {boolean} [o.quiet]     不在控制台提示
 */
export function resolveSpots(city, source, { coords = 'three', overrides = {}, include = () => true, quiet = false } = {}) {
  const defs = city.spotDefs.map((d) => ({ ...d, ...(overrides[d.id] ?? {}) }));
  const found = new Map();
  for (const d of defs) {
    const t = findAnchor(source, d, coords);
    if (t) found.set(d.id, t);
    else if (!quiet) console.warn(`[拍照·${city.name}] 找不到打卡点「${d.label}」的点位 ${names(d).join(' / ')}，先跳过`);
  }
  const spots = [];
  for (const d of defs) {
    if (!found.has(d.id) || !include(d)) continue;
    const { target, extras } = found.get(d.id);
    const spot = {
      ...d,
      ...pick(extras, ['label', 'minCoverage', 'radius']),
      target,
      facing: d.facing ? { dir: new THREE.Vector3(...d.facing.dir), maxAngle: d.facing.maxAngle } : undefined,
      // also 里写的是别的打卡点 id（比如步道地标要和歌剧院同框），换成那个点的目标
      also: (d.also ?? []).map((id) => found.get(id)?.target).filter(Boolean),
    };
    if (d.also?.length && spot.also.length < d.also.length && !quiet) {
      console.warn(`[拍照·${city.name}]「${d.label}」要同框的 ${d.also.join('、')} 没找到，同框条件先不算`);
    }
    spots.push(spot);
  }
  return spots;
}

function names(d) {
  return [d.anchor, ...(d.anchorAliases ?? [])];
}

function pick(o, keys) {
  const r = {};
  for (const k of keys) if (o?.[k] !== undefined) r[k] = o[k];
  return r;
}

// 找到一个打卡点的目标：场景里的物体（带模型就按包围盒算，空物体就按点 + 半径算），或 anchors.json 里的坐标
function findAnchor(source, d, coords) {
  if (!source) return null;
  const want = names(d);
  if (source.isObject3D) {
    let obj = null;
    source.traverse((o) => {
      if (!obj && want.some((n) => sameName(o.name, n))) obj = o;
    });
    if (!obj) return null;
    let hasMesh = false;
    obj.traverse((o) => (hasMesh ||= !!o.isMesh));
    const extras = obj.userData ?? {};
    if (hasMesh) return { target: obj, extras };
    obj.updateWorldMatrix(true, false);
    return { target: obj.getWorldPosition(new THREE.Vector3()), extras };
  }
  // anchors.json：支持 { photo_spot: [{ id, target|pos }] }、{ 名字: [x,y,z] }、{ anchors: [...] } 几种写法
  const list = [];
  const push = (name, v) => v && list.push({ name, v });
  if (Array.isArray(source.photo_spot)) for (const a of source.photo_spot) push(a.id ?? a.name, a);
  if (Array.isArray(source.anchors)) for (const a of source.anchors) push(a.name ?? a.id, a);
  else if (source.anchors && typeof source.anchors === 'object') for (const [k, v] of Object.entries(source.anchors)) push(k, v);
  for (const [k, v] of Object.entries(source)) if (/^ANCHOR_/.test(k)) push(k, v);
  const short = want.map((n) => n.replace(/^ANCHOR_photo_/, ''));
  const hit = list.find((a) => want.some((n) => sameName(a.name, n)) || short.includes(a.name) || a.name === d.id);
  if (!hit) return null;
  const v = hit.v;
  const p = Array.isArray(v) ? v : v.target ?? v.pos ?? v.position;
  if (!Array.isArray(p)) return null;
  const pos = coords === 'blender' ? new THREE.Vector3(p[0], p[2], -p[1]) : new THREE.Vector3(...p);
  return { target: pos, extras: Array.isArray(v) ? {} : v };
}

// Blender 复制出来的物体会变成 xxx.001，导出 glTF 后变成 xxx001 或 xxx_001，都认
function sameName(name, want) {
  if (!name) return false;
  if (name === want) return true;
  return name.startsWith(want) && /^[._]?\d{1,3}$/.test(name.slice(want.length));
}

/**
 * 切时段：把这座城时段表里的数值填进画面管线。
 * HdrPipeline（东京）填 exposure / bloom / lutMix；ComposerPipeline（悉尼）填 toneMappingExposure 和泛光强度。
 * 宿主自己已经在管光照和曝光的话，可以不调这个，只用 city.phases 查名字。
 */
export function applyPhase(city, key, { pipeline, renderer } = {}) {
  const ph = city.phases[key];
  if (!ph) throw new Error(`${city.name}没有这个时段：${key}`);
  if (pipeline && 'lutMix' in pipeline) {
    if (ph.exposureEv !== undefined) pipeline.exposure = 2 ** ph.exposureEv;
    if (ph.bloom !== undefined) pipeline.bloom = ph.bloom;
    if (ph.lutMix !== undefined) pipeline.lutMix = ph.lutMix;
  } else if (pipeline?.composer) {
    if (ph.toneExposure !== undefined && renderer) renderer.toneMappingExposure = ph.toneExposure;
    const bloom = pipeline.composer.passes.find((p) => 'strength' in p && p.renderTargetsHorizontal);
    if (bloom && ph.bloom !== undefined) bloom.strength = ph.bloom;
  } else if (renderer && ph.toneExposure !== undefined) {
    renderer.toneMappingExposure = ph.toneExposure;
  }
  return ph;
}

/** 一枚纪念章的图（canvas），同一个打卡点每次都一样 */
export function stampFor(city, spotOrId, size = 360) {
  const d = typeof spotOrId === 'string' ? city.spotDefs.find((s) => s.id === spotOrId) : spotOrId;
  if (!d) return null;
  return drawStamp(
    { style: city.stampStyle, id: d.id, label: d.stampLabel ?? d.label, sub: d.stampSub ?? city.stampSub, code: d.code, icon: d.icon },
    { size },
  );
}

/**
 * 集章本：记下这一城盖过哪些章。存在浏览器 localStorage 里（存不了也不影响玩，只是刷新后清空）。
 * 正式版应该由任务系统存档，这里只是个能用的默认实现。
 */
export class StampBook {
  constructor(city, { key = `cijian.stamps.${city.sceneId}` } = {}) {
    this.city = city;
    this.key = key;
    this.ids = [];
    try {
      this.ids = JSON.parse(localStorage.getItem(key) || '[]');
    } catch {}
  }
  has(id) {
    return this.ids.includes(id);
  }
  add(id) {
    if (this.has(id)) return false;
    this.ids.push(id);
    try {
      localStorage.setItem(this.key, JSON.stringify(this.ids));
    } catch {}
    return true;
  }
  clear() {
    this.ids = [];
    try {
      localStorage.removeItem(this.key);
    } catch {}
  }
  /** 按打卡点表里的顺序排好的章（必拍在前） */
  canvases(size = 360) {
    return this.city.spotDefs
      .filter((d) => this.has(d.id))
      .sort((a, b) => (b.required ? 1 : 0) - (a.required ? 1 : 0))
      .map((d) => stampFor(this.city, d, size));
  }
}

/**
 * 一步接好一座城：换焦段、找打卡点、填情境、集章、回忆卡文字。
 * @param {import('../photo.js').PhotoSystem} photo
 * @param {object} city  TOKYO / SYDNEY
 * @param {object} o
 * @param {THREE.Object3D} [o.scene]   在场景里按点位名找（默认用 photo.scene）
 * @param {object} [o.anchors]         或者用 anchors.json
 * @param {() => string} [o.getPhase]  现在的时段，city.phases 里的键
 * @param {() => string} [o.getWeather] clear / cloudy / rain
 * @param {(action: string, spot) => boolean} [o.actionDone] 剧情行动完成了没有（“完成行动后拍照才计入打卡”）；不给就当都完成了
 * @param {() => string} [o.getChoice] 当天的选择，写进回忆卡那一行字
 * @returns {{ spots, book, dispose }}
 *   拍到打卡点且行动已完成 → photo 上派发 'stamp'（detail: { spot, canvas, first }）；
 *   拍到了但行动没完成 → 派发 'stampwait'（detail: { spot }），可以提示“先去录音”。
 */
export function setupCity(photo, city, o = {}) {
  photo.setFocalLengths(city.focalLengths);
  const spots = resolveSpots(city, o.anchors ?? o.scene ?? photo.scene, o);
  photo.spots = spots;
  const phase = () => o.getPhase?.() ?? city.defaultPhase;
  photo.getContext = () => ({ sceneId: city.sceneId, phase: phase(), weather: o.getWeather?.() ?? 'clear' });
  const book = o.book ?? new StampBook(city);
  const actionDone = o.actionDone ?? (() => true);
  const onPhoto = (e) => {
    for (const id of e.detail.record.meta.spotHits) {
      const spot = spots.find((s) => s.id === id);
      if (!spot) continue;
      if (spot.action && !actionDone(spot.action, spot)) {
        photo.dispatchEvent(new CustomEvent('stampwait', { detail: { spot } }));
        continue;
      }
      const first = book.add(id);
      photo.dispatchEvent(new CustomEvent('stamp', { detail: { spot, first, canvas: stampFor(city, spot) } }));
    }
  };
  photo.addEventListener('photo', onPhoto);
  photo.album.cardInfo = (picked) => cardInfo(city, picked, { book, choice: o.getChoice?.() });
  return { spots, book, dispose: () => photo.removeEventListener('photo', onPhoto) };
}

/** 按城市的回忆卡模板填文字，附上集到的章 */
export function cardInfo(city, picked, { book, choice } = {}) {
  const first = picked[0]?.meta ?? {};
  const d = first.createdAt ? new Date(first.createdAt) : new Date();
  const spotIds = picked.flatMap((p) => p.meta.spotHits ?? []);
  const fill = {
    date: `${d.getMonth() + 1}月${d.getDate()}日`,
    weather: WEATHER[first.weather] ?? first.weather ?? '晴',
    phase: city.phases[first.phase]?.label ?? '',
    place: city.card.place,
    choice: choice ?? '',
    spots: spotIds.map((id) => city.spotDefs.find((s) => s.id === id)?.label).filter(Boolean),
    hasSunset: spotIds.includes(city.card.sunsetSpot),
  };
  const t = city.card;
  return {
    title: typeof t.title === 'function' ? t.title(fill) : t.title,
    subtitle: typeof t.subtitle === 'function' ? t.subtitle(fill) : t.subtitle,
    caption: t.caption(fill),
    sealText: t.sealText ?? '此间',
    stamps: book ? book.canvases() : [],
  };
}
