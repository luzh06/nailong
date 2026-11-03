// 悉尼 · Noah 线《拍照的人也在照片里》的拍照配置（北岸 Kirribilli / Milsons Point 远眺）。
// 打卡点是「预览提案」（见 此间_打卡点预览_东京悉尼.md）；S5—S7 用户已定为必拍（2026-11-03）。改这个文件就行。
//
// 坐标：原点在歌剧院，x 东、y 上、−z 北（sydney-harbour 网页的坐标）。
// 用法：
//   const pipeline = sydneyPipeline(renderer, post.composer);      // 用悉尼原有的 composer
//   const photo = new PhotoSystem({ ...SYDNEY, renderer, scene, camera, pipeline });
//   setupSydney(photo, { getPhase: () => phase, actionDone: (a) => quest.done(a) });
import * as THREE from 'three';
import { ComposerPipeline } from '../../render/pipeline.js';
import { setupCity, applyPhase } from './common.js';

export const SYDNEY = {
  // ---- 这几项 PhotoSystem 直接认 ----
  styleId: 'rangefinder',             // Noah 推荐的相机
  focalLengths: [28, 50, 85, 135],    // 隔着海看歌剧院（约 1 公里）要 135mm；咖啡店里合影要 28mm
  spots: [],

  // ---- 给 setupSydney / 任务系统 / 回忆卡用 ----
  sceneId: 'sydney',
  name: '悉尼',
  character: 'noah',
  story: '拍照的人也在照片里',
  defaultPhase: 'day',
  stampStyle: 'trail',
  stampSub: '北岸步道 · 此间',

  // 时段：悉尼有白天 / 黄金时段 / 蓝调三档。toneExposure 是 renderer.toneMappingExposure，bloom 是 UnrealBloomPass 强度。
  // 这些数是测试页上调的兜底值；悉尼工程自己的光照代码已经设了曝光的话，以它为准，不必调 applySydneyPhase。
  phases: {
    day: { label: '白天', toneExposure: 1.0, bloom: 0.2 },
    golden: { label: '黄金时段', toneExposure: 1.0, bloom: 0.2 },
    blue: { label: '蓝调', toneExposure: 1.15, bloom: 0.2 },
  },

  spotDefs: [
    {
      id: 'sy_cafe', code: 'S1', required: true, label: 'Maya 的咖啡店', anchor: 'ANCHOR_photo_cafe',
      anchorAliases: ['ANCHOR_photo_group'],   // 第一天执行整合文档里写的是 group，两个名字都认
      story: '告别相册第 1 张：朋友们的合影（拍前先问“可以拍吗”）', action: 'ask_group',
      needSubjects: ['maya'],                  // 合影里要拍到 Maya，而且问过她
      minCoverage: 0.06, radius: 3, suggest: '28mm 横拍', tip: '大家都看着你', icon: 'cafe',
    },
    {
      id: 'sy_landmark', code: 'S2', required: true, label: '步道地标', anchor: 'ANCHOR_photo_landmark',
      story: '告别相册第 2 张：Tess 指出的地标', action: 'meet_tess',
      minCoverage: 0.03, radius: 1.5, also: ['sy_opera'], suggest: '50–85mm', tip: '远处的歌剧院也在画里', icon: 'marker',
    },
    {
      id: 'sy_bench', code: 'S3', required: true, label: 'Sam 的长椅', anchor: 'ANCHOR_photo_bench',
      story: '告别相册第 3 张：朋友常坐的长椅', action: 'bench_story',
      minCoverage: 0.04, radius: 1.2, suggest: '50mm', icon: 'bench',
    },
    {
      id: 'sy_shore', code: 'S4', required: true, label: '黄昏的海', anchor: 'ANCHOR_photo_shore',
      story: '第一天收尾：黄昏拍海，地图页“海岸”显影', action: 'deliver',
      minCoverage: 0.03, radius: 60, phases: ['golden'], suggest: '28mm 横拍',
      waitTip: '黄金时段再来', bookmark: '第一次日落。你的旅行页，显影了一角。', icon: 'shore',
    },
    {
      id: 'sy_opera', code: 'S5', required: true, label: '歌剧院', anchor: 'ANCHOR_photo_opera',
      story: '远景地标', minCoverage: 0.04, radius: 45, suggest: '135mm', tip: '长焦把它拉近', icon: 'opera', stampLabel: '远方的帆',
    },
    {
      id: 'sy_bridge', code: 'S6', required: true, label: '海港大桥', anchor: 'ANCHOR_photo_bridge',
      // 大桥离步道只有约 500 米、连引桥一千多米，什么焦段都装不下一半；拍一段拱也算好照片，所以不要求露出比例
      story: '远景地标', minCoverage: 0.06, minVisible: 0, radius: 120, suggest: '28mm 拍全景，85–135mm 拍一段拱', icon: 'bridge', stampLabel: '拱桥',
    },
    {
      id: 'sy_bluehour', code: 'S7', required: true, label: '蓝调时分', anchor: 'ANCHOR_photo_bluehour',
      story: '亮灯的大桥或城区，蓝调时段才算', minCoverage: 0.04, radius: 150, phases: ['blue'],
      suggest: '50–85mm，−1/3 EV', tip: (p) => (p.ev <= -0.3 ? '灯亮了' : '按 ↓ 减 1/3 档，保住灯光'), waitTip: '蓝调时分再来', icon: 'bluehour',
    },
  ],

  // 可能入镜的人（预览提案），说明见 tokyo.js 的 people
  people: [
    { id: 'noah', label: 'Noah', avatar: true },
    { id: 'maya', label: 'Maya', node: 'NPC_maya', needsConsent: true, story: '咖啡店的合影，拍前先问' },
    { id: 'camille', label: 'Camille', node: 'NPC_camille' },
  ],

  card: {
    title: '拍照的人也在照片里',
    subtitle: '三日归途 · 第一天 · 悉尼',
    place: '北岸',
    sunsetSpot: 'sy_shore',
    caption: (f) => [f.date, f.weather, f.place, f.choice || (f.hasSelfie ? '这次，我也在照片里' : f.hasSunset ? '在海边等到了黄昏' : '替朋友们补拍了告别相册')].join(' · '),
  },
};

/**
 * 画面管线：悉尼用它自己的 EffectComposer（RenderPass → UnrealBloomPass(0.2, 0.55, 1.0) → OutputPass，ACES）。
 * 有现成的 composer 就传进来（推荐，不用改 post.js）；没有就按同样的参数搭一条。
 */
export async function createSydneyPipeline(renderer, scene, camera, { composer = null } = {}) {
  if (composer) return new ComposerPipeline(renderer, composer);
  const { EffectComposer } = await import('three/addons/postprocessing/EffectComposer.js');
  const { RenderPass } = await import('three/addons/postprocessing/RenderPass.js');
  const { UnrealBloomPass } = await import('three/addons/postprocessing/UnrealBloomPass.js');
  const { OutputPass } = await import('three/addons/postprocessing/OutputPass.js');
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  const size = renderer.getSize(new THREE.Vector2());
  const c = new EffectComposer(renderer, new THREE.WebGLRenderTarget(size.x, size.y, { type: THREE.HalfFloatType, samples: 4 }));
  c.addPass(new RenderPass(scene, camera));
  c.addPass(new UnrealBloomPass(size.clone().multiplyScalar(0.5), 0.2, 0.55, 1.0));
  c.addPass(new OutputPass());
  return new ComposerPipeline(renderer, c);
}

export function setupSydney(photo, o = {}) {
  return setupCity(photo, SYDNEY, o);
}

export function applySydneyPhase(key, o) {
  return applyPhase(SYDNEY, key, o);
}
