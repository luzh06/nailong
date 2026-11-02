# cijian-app：《三日归途》游戏程序

这里将来是唯一的游戏程序（Three.js r170），见 `此间_第一天执行整合文档.md` 第 2 节。
**目前只有拍照模块和它的测试页。** 流程、人物、任务、场景加载都还没写。

## 拍照模块 `src/photo/`

设计依据：`此间_剧情与整合方案_v0.2.md` 模块 5、`此间_相机.md`。

整条线：**取景 → 快门 → 离屏截图 → 存 IndexedDB → 相册 → 回忆卡 → 下载**。

| 文件 | 内容 |
|---|---|
| `photo.js` | `PhotoSystem`：取景模式、焦段、快门、截图、照片元信息、按键 |
| `grade.js` | 调色通道：色调映射 + sRGB + 相机风格调色（可选 `.cube` LUT）。预览和拍照共用，所见即所得 |
| `styles.js` | 两台相机的风格参数、四档焦段 |
| `store.js` | IndexedDB 存储；隐私模式等不可用时退回内存并提示 |
| `album.js` | 相册、显影动画、回忆卡界面 |
| `card.js` | 冲印（相纸边）和回忆卡合成，视觉沿用 `poster/make_poster.py` |
| `sound.js` | 快门声（WebAudio 合成的占位声，正式音效到了再换） |
| `photo.css` | 取景框、快门光圈、显影、相册样式 |

### 接进游戏只要三处
```js
import { PhotoSystem } from './photo/photo.js';
const photo = new PhotoSystem({
  renderer, scene, camera,
  styleId: 'instant',                       // 图书馆里选的相机：'instant' 或 'rangefinder'
  getContext: () => ({ sceneId: 'tokyo', spotId: 当前打卡点或null, phase: 'day', weather: 'clear' }),
});
// 1. 每帧
if (!photo.render()) renderer.render(scene, camera);
// 2. 取景时人物停下（视角照常转）
if (!photo.active) player.update(dt);
// 3. 不想出现在照片里的提示物体
marker.userData.hideInPhoto = true;
```
- 事件：`photo` 每拍一张（`detail.record` 有 `meta` 和 `blob`，任务系统用它判断打卡）、`error` 截图失败、`card` 生成了回忆卡。
- 回忆卡文字：`photo.album.cardInfo = (picked) => ({ title, subtitle, caption, sealText })`。
- 界面上带 `data-hud` 的元素在取景时自动隐藏。
- 按键（`bindKeys: true` 时）：C 或右键 取景，单击（不拖动）或空格 快门，滚轮 焦段，B 相册，Esc 退出。

### 照片元信息
`{ id, createdOrder, createdAt, sceneId, spotId, phase, weather, cameraStyle, camera: { position, quaternion, focalMm } }`
`camera` 留给以后的“点照片回到当时现场”。

## 测试页
```bash
cd projects/cijian-app && python3 -m http.server 8766
```
打开 http://127.0.0.1:8766/photo-test.html 。场景是程序生成的小街，只用来测拍照，不是正式美术。
Three.js 用本目录 `vendor/three.module.js`（r170，从 `yuyake-dandan` 复制，MIT）。

## 已验证（2026-11-02，Mac M2，Claude 应用内置浏览器）
- 取景框比例、焦段视角和拍出的照片一致；交互标记 `hideInPhoto` 没出现在照片里。
- 即时成像 3000×3000、胶片旁轴 3000×2000 的 JPEG 能解码；冲印版和回忆卡 PNG（1600×2200）存成文件后打开正常。
- 一次拍照从按快门到存好约 0.8 秒，显影小图在 0.4 秒内出现。

**没验证：**
- 内置浏览器不把下载存到磁盘，所以“点下载按钮 → 打开文件”要在 Chrome 里再点一次确认。
- 没在 5070 上测帧率；没接真实东京场景（色调映射是否一致要接上后对比）。

## 临时的东西（之后要换）
- 两台相机的调色数值是临时的，要拿东京 Cycles 渲染图对照调，最好导出成 `.cube` 填进 `styles.js` 的 `lut`。
- 快门声是合成的占位声。
- 中文字体用系统宋体兜底；正式版要用思源宋体子集（见 `此间_相机.md` 3.5 节）。
- 宿主渲染器用 AgX 色调映射时，拍照暂时按 ACES 处理，颜色会略有差别。

## 还没做
景深和点击对焦、打卡盖章、快门转场（切时段）、点照片回到现场、换相机菜单（现在只能代码里 `setStyle`）。
