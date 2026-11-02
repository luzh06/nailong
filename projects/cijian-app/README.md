# cijian-app：《三日归途》游戏程序

这里将来是唯一的游戏程序（Three.js r170），见 `此间_第一天执行整合文档.md` 第 2 节。
**目前有：画面管线 `src/render/` 和拍照模块 `src/photo/`，以及拍照测试页。** 流程、人物、任务、场景加载还没写。

## 画面管线 `src/render/pipeline.js`

照片和屏幕颜色一致的前提是：**游戏画屏幕和拍照用同一条管线**。

| 类 | 用在哪 |
|---|---|
| `HdrPipeline` | 烘焙场景（东京、悉尼、图书馆）。和烘焙小样 `projects/cijian-5070/web/game.js` 的后期**逐行一致**：HDR 目标（4×MSAA）→ 6 级泛光 → 曝光 → AgX 查找表（log2 编码，48³，两张可混合）→ 抖动 |
| `StandardPipeline` | 没有自定义后期的场景，用 Three.js 自带色调映射 |

两者接口相同：`render(scene, camera, target = null, { width, height })`，`target` 为 null 时画到屏幕。
宿主若有自己的后期，提供同样签名的 `render`（能画到任意大小的 target，输出显示色）也能接。

```js
import { HdrPipeline } from './render/pipeline.js';
const pipeline = new HdrPipeline(renderer);              // 会把 renderer 设成 NoToneMapping + 线性输出
pipeline.setLuts(await pipeline.loadLut('data/lut_morning.bin'), await pipeline.loadLut('data/lut_sunset.bin'));
pipeline.exposure = 2 ** 0.3;  // game.js 里 LIGHT.exposure 是 EV，这里填倍数
pipeline.bloom = 0.2;
pipeline.lutMix = 1;           // 0 = 第一张查找表（早晨），1 = 第二张（日落），中间是过渡
// 每帧
pipeline.render(scene, camera);
```
场景材质、天空、雾这些照搬 game.js 即可，管线只负责“场景 HDR 之后”的部分。

## 拍照模块 `src/photo/`

设计依据：`此间_剧情与整合方案_v0.2.md` 模块 5、`此间_相机.md`。
整条线：**取景 → 快门 → 离屏截图 → 存 IndexedDB → 相册 → 回忆卡 → 下载**。

### 接进游戏
```js
import { PhotoSystem } from './photo/index.js';     // 样式表会自动加载，不用另引 CSS

const photo = new PhotoSystem({
  renderer, scene, camera,
  pipeline,                                          // 上面那条管线；不给就用 StandardPipeline
  styleId: 'instant',                                // 图书馆里选的相机：'instant' 或 'rangefinder'
  spots: [                                           // 本城的打卡点（可选）
    { id: 'tk_stairs', target: stairsObject, minCoverage: 0.03 },
    { id: 'tk_shop',   target: new THREE.Vector3(x, y, z), radius: 1.5 },
  ],
  getContext: () => ({ sceneId: 'tokyo', phase: 'sunset', weather: 'clear' }),
  // keys: { toggle: 'KeyC', shoot: 'Space', album: 'KeyB', exit: 'Escape' },  // 可改
  // captureLongSide: 3000,
});

// 每帧：取景时由拍照模块画这一帧
if (!photo.render()) pipeline.render(scene, camera);

// 人物控制：取景时人物停下，转视角灵敏度乘 lookScale（长焦时自动变慢）
if (!photo.active) player.update(dt);
yaw -= mouseDX * sensitivity * photo.lookScale;

// 第三人称：取景是第一人称，进出时宿主自己切镜头、藏人物
photo.addEventListener('enter', () => { avatar.visible = false; camera.position.copy(eyePosition); });
photo.addEventListener('exit',  () => { avatar.visible = true; });

// 宿主自己改了 camera.fov 或窗口大小变了
photo.relayout();

// 不该出现在照片里的提示物体（交互光圈、任务标记）
marker.userData.hideInPhoto = true;

// 任务系统：每拍一张都会收到，spotHits 是这张拍到的打卡点
photo.addEventListener('photo', (e) => {
  const { meta } = e.detail.record;
  if (meta.spotHits.includes('tk_stairs') && quest.actionDone('tk_stairs')) stamp('tk_stairs');
});
```

- **打卡判定** `photo.checkSpot(spot)`：目标在画面里、没被挡住（从相机向目标中心打射线）、占画面比例 ≥ `minCoverage`（默认 2%）才算。剧情规定“完成行动后拍照才计入打卡”，所以盖不盖章由任务系统结合 `spotHits` 决定，模块只负责“拍没拍到”。
- **事件**：`photo`（拍好一张）、`error`（截图失败，`detail.message` 可直接给玩家看）、`card`（生成了回忆卡）、`enter` / `exit`、`stylechange`。
- **回忆卡文字**：`photo.album.cardInfo = (picked) => ({ title, subtitle, caption, sealText })`。
- 带 `data-hud` 的界面元素取景时自动隐藏。
- 默认按键：C 或右键 取景，单击（不拖动）或空格 快门，滚轮 焦段（24/35/50/85mm），B 相册，Esc 退出。在 pointer lock 下单击也是快门。

### 照片元信息
`{ id, createdOrder, createdAt, sceneId, spotId, spotHits, phase, weather, cameraStyle, camera: { position, quaternion, focalMm } }`
`camera` 留给以后的“点照片回到当时现场”。

### 文件
| 文件 | 内容 |
|---|---|
| `index.js` | 统一入口 |
| `photo.js` | `PhotoSystem`：取景、焦段、快门、截图、打卡判定、按键 |
| `grade.js` | 相机风格调色，在管线输出的显示色上做；预览和拍照共用 |
| `styles.js` | 两台相机的参数 |
| `store.js` / `album.js` / `card.js` | 存储、相册、冲印和回忆卡 |
| `sound.js` / `photo.css` | 快门声（占位）、界面样式 |

## 测试页
```bash
cd projects/cijian-app && python3 -m http.server 8766
```
打开 http://127.0.0.1:8766/photo-test.html （改过代码后用 Cmd+Shift+R 强制刷新，否则浏览器会用旧文件）。
场景是程序生成的小街，只用来测拍照，不是正式美术。

测试页默认用 `HdrPipeline`，查找表从 `test-data/lut_morning.bin`、`test-data/lut_sunset.bin` 读：
就是 `projects/cijian-5070/web/data/` 里的同名文件（Git LFS），复制过来即可，`test-data/` 不入库。
没有这两个文件时自动退回 `StandardPipeline`；`?pipeline=standard` 可强制用后者。

## 已验证（2026-11-03，Mac M2，Claude 应用内置浏览器）
- **照片和屏幕颜色一致**：关掉相机风格后，同一机位 2048×1536（屏幕）和 3000×2250（照片）逐块比较（8×8 区块），白天最大差 0.23/255，日落（有泛光）最大差 0.52/255。为此把泛光链改成始终按屏幕分辨率起步，否则照片的泛光会偏小（差约 5/255）。
- 取景框比例、焦段视角和拍出的照片一致；`hideInPhoto` 的物体不进照片。
- 打卡判定四种情况都对：正对 ✓、背对 ✗、太远（占 0.6%）✗、被房子挡住 ✗；真拍时 `spotHits` 正确。
- 即时成像 3000×3000、胶片旁轴 3000×2000 的 JPEG，冲印版和回忆卡 PNG 存成文件后打开正常。
- 一次拍照从按快门到存好约 0.8 秒，显影小图 0.4 秒内出现。

**没验证：**
- 没接真实东京场景（要下约 477MB 的烘焙包，本机磁盘和网络都不够）。管线数学和 game.js 一致，但相机风格是在测试小街上调的，接上真场景后要再看一眼。
- 没在 5070 上测帧率。取景时每帧多两次全屏调色，预计影响很小。
- 内置浏览器不把下载存到磁盘，“点下载按钮 → 打开文件”要在 Chrome 里点一次确认。

## 临时的东西（之后要换）
- 两台相机的调色数值：要拿东京烘焙场景再看一遍，满意后可以导出成 `.cube` 填进 `styles.js` 的 `lut`。
- 快门声是合成的占位声；中文字体用系统宋体兜底，正式版用思源宋体子集（`此间_相机.md` 3.5 节）。

## 还没做
景深和点击对焦、快门转场（切时段）、点照片回到现场、换相机菜单（现在用 `photo.setStyle()`）、纪念章图案。
