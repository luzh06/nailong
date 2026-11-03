// 各城的拍照配置。游戏里按城市取：CITIES[sceneId]。
export { TOKYO, setupTokyo, createTokyoPipeline, applyTokyoPhase } from './tokyo.js';
export { SYDNEY, setupSydney, createSydneyPipeline, applySydneyPhase } from './sydney.js';
export { resolveSpots, resolveSubjects, applyPhase, setupCity, cardInfo, stampFor, StampBook } from './common.js';
import { TOKYO } from './tokyo.js';
import { SYDNEY } from './sydney.js';

export const CITIES = { tokyo: TOKYO, sydney: SYDNEY };
