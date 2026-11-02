// 拍照模块的统一入口：游戏里只 import 这一个文件。
export { PhotoSystem } from './photo.js';
export { CAMERA_STYLES, FOCAL_LENGTHS } from './styles.js';
export { composeMemoryCard, framePhoto, downloadBlob } from './card.js';
export { drawStamp } from './stamps.js';
export { ALBUM_LIMIT } from './store.js';
export { HdrPipeline, StandardPipeline, ComposerPipeline } from '../render/pipeline.js';
