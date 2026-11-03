// 东京 · 凛线《寄给明天的声音》的拍照配置（谷中 + 浅草寺拼接）。
// 打卡点是「预览提案」（见 此间_打卡点预览_东京悉尼.md），名字、数量、点位都等用户拍板，改这个文件就行。
//
// 坐标沿用 qs_h1 世界系：Blender (x, y, z) → three (x, z, −y)，原点在台阶顶。
// 用法：
//   const photo = new PhotoSystem({ ...TOKYO, renderer, scene, camera, pipeline });
//   setupTokyo(photo, { getPhase: () => phase, actionDone: (a) => quest.done(a) });
import { HdrPipeline } from '../../render/pipeline.js';
import { setupCity, applyPhase } from './common.js';

// 夕阳方向：按 cijian-5070/web/game.js 的 LIGHT.sunset（az 268°，el 6.1°）和它的 sunDir() 换算成 three 坐标（只取水平方向）。
// 接上真场景后若看着不对，改这里。
const SUNSET_DIR = [0.035, 0, 0.999];

// 竖向主体的提示：方画幅（即时成像）没有横竖之分，就不提“按 R 竖拍”
const upTip = (rest) => (p) => (p.frameAspect === 1 || p.portrait ? rest : `按 R 竖拍，${rest}`);

export const TOKYO = {
  // ---- 这几项 PhotoSystem 直接认 ----
  styleId: 'instant',                 // 凛推荐的相机；玩家在图书馆选了别的就用玩家选的
  focalLengths: [24, 35, 50, 85],     // 谷中街宽只有几米，要 24mm；85mm 拍提灯、塔檐的局部
  spots: [],                          // 由 setupTokyo() 按点位名找好后填进去

  // ---- 下面是给 setupTokyo / 任务系统 / 回忆卡用的 ----
  sceneId: 'tokyo',
  name: '东京',
  character: 'rin',
  story: '寄给明天的声音',
  defaultPhase: 'day',
  stampStyle: 'station',
  stampSub: '谷中 · 此間',

  // 时段：数值照搬 game.js 的 LIGHT（exposure 是 EV，bloom 同 game.js），lutMix 0 = 早晨查找表、1 = 日落查找表
  phases: {
    day: { label: '白天', exposureEv: 0.5, bloom: 0, lutMix: 0 },
    sunset: { label: '日落', exposureEv: 0.3, bloom: 0.2, lutMix: 1 },
  },

  /**
   * 打卡点。必拍 = 剧情任务；可选 = 逛街奖励，拍到会多一枚章。
   *   anchor        Blender 里空物体的名字（导出后代码按名字找）
   *   action        要先完成的剧情行动（任务系统里的 id），没完成拍到也不盖章
   *   minCoverage   最小占画面比例；radius 是点位为空物体时按多大的球算（米）
   *   minVisible    主体至少露出多少在画面里（默认 0.5，凑太近只拍到一角不算）
   *   phases        只在这些时段拍才算；facing 镜头要大致朝这个方向
   *   tip           取景框里地点名下面的小字；waitTip 时段不对时显示
   *   icon          纪念章中间的线描（stamps.js 里的 ICONS）
   */
  spotDefs: [
    {
      id: 'tk_haruka', code: 'T1', required: true, label: '遥的店', anchor: 'ANCHOR_photo_haruka',
      story: '录音 1：店门口的风铃。先录音再拍', action: 'rec_bell',
      minCoverage: 0.04, radius: 2.2, suggest: '35mm 横拍', icon: 'record',
    },
    {
      id: 'tk_hiyori', code: 'T2', required: true, label: '喫茶 ひより', anchor: 'ANCHOR_photo_hiyori',
      story: '录音 2：杯碟相碰的声音，可能遇到美绪', action: 'rec_cafe',
      minCoverage: 0.04, radius: 2.2, suggest: '24–35mm', icon: 'cup',
    },
    {
      id: 'tk_yaomasa', code: 'T3', required: true, label: '八百政', anchor: 'ANCHOR_photo_yaomasa',
      story: '录音 3：路人一句“谢谢”', action: 'rec_thanks',
      minCoverage: 0.04, radius: 2.2, suggest: '35mm', icon: 'veg',
    },
    {
      id: 'tk_dandan', code: 'T4', required: true, label: '夕焼けだんだん', anchor: 'ANCHOR_photo_dandan',
      story: '第一天收尾：台阶顶拍日落，地图页“声音”显影', action: 'deliver',
      // 这张拍的是“从台阶顶往下看的那一眼”，台阶本身大半在画面下沿外，所以露出比例放宽到 5%
      minCoverage: 0.03, minVisible: 0.05, radius: 3, phases: ['sunset'], facing: { dir: SUNSET_DIR, maxAngle: 70 },
      tip: (p) => (p.ev >= 0.6 ? '第一次日落' : '逆光，按 ↑ 加 2/3 档会更透'), waitTip: '等日落时再来', suggest: '24mm，可低角度',
      bookmark: '第一次日落。你的旅行页，显影了一角。', icon: 'stairs',
    },
    {
      id: 'tk_kaminarimon', code: 'T5', required: false, label: '雷门大提灯', anchor: 'ANCHOR_photo_kaminarimon',
      story: '逛街奖励', minCoverage: 0.06, radius: 2, tip: upTip('往上仰更好看'), icon: 'lantern', stampSub: '浅草 · 此間',
    },
    {
      id: 'tk_pagoda', code: 'T6', required: false, label: '五重塔', anchor: 'ANCHOR_photo_pagoda',
      story: '逛街奖励', minCoverage: 0.08, radius: 8, tip: upTip('24mm 加低角度（V）'), icon: 'pagoda', stampSub: '浅草 · 此間',
    },
    {
      id: 'tk_poles', code: 'T7', required: false, label: '电线杆与天空', anchor: 'ANCHOR_photo_poles',
      story: '逛街奖励', minCoverage: 0.05, radius: 4, tip: upTip('往上仰，留一片天'), icon: 'poles',
    },
  ],

  // 回忆卡文字：caption 拿到 { date, weather, phase, place, choice, spots, hasSunset }
  // 可能入镜的人（预览提案）。avatar = 这座城的玩家人物；node = 场景里人物模型的名字（宿主也可以直接传物体）。
  // needsConsent：剧情要求拍之前先问“可以拍吗”，没问就拍，照片照样留着但不算进剧情。
  people: [
    { id: 'rin', label: '凛', avatar: true },
    { id: 'linchuan', label: '林川', node: 'NPC_linchuan' },
    { id: 'passerby', label: '路过的人', node: 'NPC_passerby', needsConsent: true, story: '录音 3 里说“谢谢”的路人' },
  ],

  card: {
    title: '寄给明天的声音',
    subtitle: '三日归途 · 第一天 · 东京',
    place: '谷中',
    sunsetSpot: 'tk_dandan',
    caption: (f) => [f.date, f.weather, f.place, f.choice || (f.hasSunset ? '看了第一次日落' : '留下了一段店里的声音')].join(' · '),
  },
};

/**
 * 画面管线：东京用烘焙小样同款（HDR → 泛光 → 曝光 → AgX 查找表），照片和屏幕颜色一致。
 * @param {string} [o.lutBase] 查找表所在目录（lut_morning.bin、lut_sunset.bin）
 */
export async function createTokyoPipeline(renderer, { lutBase = 'data/' } = {}) {
  const p = new HdrPipeline(renderer);
  const [a, b] = await Promise.all([p.loadLut(`${lutBase}lut_morning.bin`), p.loadLut(`${lutBase}lut_sunset.bin`)]);
  p.setLuts(a, b);
  return p;
}

/** 一步接好东京：见 common.js 的 setupCity */
export function setupTokyo(photo, o = {}) {
  return setupCity(photo, TOKYO, o);
}

export function applyTokyoPhase(key, o) {
  return applyPhase(TOKYO, key, o);
}
