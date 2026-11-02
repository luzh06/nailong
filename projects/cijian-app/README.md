# cijian-app：《三日归途》游戏程序

这里将来是唯一的游戏程序（Three.js r170），见 `此间_第一天执行整合文档.md` 第 2 节。
**目前有：画面管线 `src/render/`、拍照模块 `src/photo/`（含东京、悉尼两套配置 `src/photo/presets/`）、拍照测试页。** 流程、人物、任务、场景加载还没写。

> 只想知道东京、悉尼怎么接？直接看下面「[东京和悉尼：几行接好](#东京和悉尼几行接好)」。

## 画面管线 `src/render/pipeline.js`

照片和屏幕颜色一致的前提是：**游戏画屏幕和拍照用同一条管线**。

| 类 | 用在哪 |
|---|---|
| `HdrPipeline` | 东京（谷中）、图书馆这类用烘焙小样那套后期的场景。和 `projects/cijian-5070/web/game.js` 的后期**逐行一致**：HDR 目标（4×MSAA）→ 6 级泛光 → 曝光 → AgX 查找表（log2 编码，48³，两张可混合）→ 抖动 |
| `ComposerPipeline` | 用 Three.js `EffectComposer` 的场景，比如悉尼（`sydney-harbour/web/src/post.js`：RenderPass → UnrealBloomPass → OutputPass） |
| `StandardPipeline` | 没有自定义后期的场景，用 Three.js 自带色调映射 |

三者接口相同：`render(scene, camera, target = null, { width, height })`，`target` 为 null 时画到屏幕。
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

悉尼直接用它已有的 composer，不用改 post.js：
```js
import { ComposerPipeline } from './render/pipeline.js';
const post = createPost(renderer, scene, camera, quality);      // sydney-harbour 原有代码
const pipeline = new ComposerPipeline(renderer, post.composer);
// 每帧把 post.composer.render() 换成：
if (!photo.render()) pipeline.render(scene, camera);
```
拍 3000 像素大照片时，composer 会临时改到照片尺寸、泛光仍按屏幕分辨率算，拍完恢复原尺寸。

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
  focalLengths: [24, 35, 50, 85],                    // 东京窄街要 24mm；悉尼远眺用 [28, 50, 85, 135]
  spots: [                                           // 本城的打卡点（可选），label 会在取景框里显示
    { id: 'tk_stairs', label: '夕焼けだんだん', target: stairsObject, minCoverage: 0.03 },
    { id: 'tk_lantern', label: '雷门大提灯', target: new THREE.Vector3(x, y, z), radius: 2 },
  ],
  occluders: [collisionMesh],                        // 判断“被挡住”用的低面数模型；不给就用整个场景（东京约 230 万面，慢）
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
- 默认按键：C 或右键 取景，单击（不拖动）或空格 快门，滚轮 焦段，B 相册，Esc 退出；取景时 R 横拍/竖拍，V 低角度，↑↓ 或 Shift+滚轮 曝光补偿。全部可用 `keys` 改。在 pointer lock 下单击也是快门。
- 换城市时：`photo.setFocalLengths([...])`、改 `photo.spots`、必要时换 `photo.pipeline`。

### 东京和悉尼：几行接好

每座城市的打卡点、焦段、默认相机、时段、回忆卡文字、纪念章样式，都写在一个文件里：
- 东京：`src/photo/presets/tokyo.js`（凛线《寄给明天的声音》）
- 悉尼：`src/photo/presets/sydney.js`（Noah 线《拍照的人也在照片里》）

**东京**（烘焙小样那套画面）：
```js
import { PhotoSystem } from './photo/index.js';
import { TOKYO, setupTokyo, createTokyoPipeline, applyTokyoPhase } from './photo/presets/index.js';

const pipeline = await createTokyoPipeline(renderer, { lutBase: 'data/' });  // 读 lut_morning.bin、lut_sunset.bin
const photo = new PhotoSystem({ ...TOKYO, renderer, scene, camera, pipeline, styleId: 玩家选的相机 });
const tokyo = setupTokyo(photo, {
  getPhase: () => 当前时段,                      // 'day' 或 'sunset'
  actionDone: (action) => quest.isDone(action),  // 剧情行动做完没有，比如 'rec_bell'（先录风铃，再拍才盖章）
});
applyTokyoPhase('sunset', { pipeline });         // 切时段时调用（曝光、泛光、查找表照 game.js）
```

**悉尼**（用它原来的 EffectComposer，不用改 post.js）：
```js
import { SYDNEY, setupSydney, createSydneyPipeline } from './photo/presets/index.js';
const pipeline = await createSydneyPipeline(renderer, scene, camera, { composer: post.composer });
const photo = new PhotoSystem({ ...SYDNEY, renderer, scene, camera, pipeline, styleId: 玩家选的相机 });
setupSydney(photo, { getPhase: () => 当前时段 /* 'day' | 'golden' | 'blue' */, actionDone: (a) => quest.isDone(a) });
```

然后每帧照旧：`if (!photo.render()) pipeline.render(scene, camera);`

`setupTokyo` / `setupSydney` 一步做完这些事：
- 换成这座城的焦段：东京 24/35/50/85，悉尼 28/50/85/135。
- 在场景里按名字找打卡点。
- 填好拍照情境（城市、时段、天气）。
- 集纪念章。
- 设好回忆卡文字，并把集到的章印在回忆卡上。

拍到打卡点时，`photo` 上会多出两个事件：
```js
photo.addEventListener('stamp', (e) => { /* e.detail: { spot, first, canvas } —— canvas 就是那枚章的图，可以直接贴到书签地图页 */ });
photo.addEventListener('stampwait', (e) => { /* 拍到了，但那里的剧情行动还没做，比如提示“先去录音” */ });
```
集章默认存在浏览器里（`StampBook`，localStorage）。正式版应该交给任务系统存档：给 `setupCity` 传 `book`，或者监听 `stamp` 自己存。

#### 打卡点（预览提案，等用户拍板）

依据 `此间_打卡点预览_东京悉尼.md`。“必拍”是剧情任务，“可选”是逛街奖励。

| 城市 | 编号 | 名字 | 点位名（Blender 里的空物体） | 要先完成的行动 | 特别条件 |
|---|---|---|---|---|---|
| 东京 | T1 | 遥的店 | `ANCHOR_photo_haruka` | `rec_bell` | |
| 东京 | T2 | 喫茶 ひより | `ANCHOR_photo_hiyori` | `rec_cafe` | |
| 东京 | T3 | 八百政 | `ANCHOR_photo_yaomasa` | `rec_thanks` | |
| 东京 | T4 | 夕焼けだんだん | `ANCHOR_photo_dandan` | `deliver` | 只在日落算；镜头要大致朝着夕阳 |
| 东京 | T5—T7 | 雷门大提灯 / 五重塔 / 电线杆与天空（可选） | `ANCHOR_photo_kaminarimon` / `_pagoda` / `_poles` | 无 | |
| 悉尼 | S1 | Maya 的咖啡店 | `ANCHOR_photo_cafe`（也认 `ANCHOR_photo_group`） | `ask_group` | |
| 悉尼 | S2 | 步道地标 | `ANCHOR_photo_landmark` | `meet_tess` | 远处的歌剧院也要在画面里 |
| 悉尼 | S3 | Sam 的长椅 | `ANCHOR_photo_bench` | `bench_story` | |
| 悉尼 | S4 | 黄昏的海 | `ANCHOR_photo_shore` | `deliver` | 只在黄金时段算 |
| 悉尼 | S5—S7 | 歌剧院 / 海港大桥 / 蓝调时分（用户已定为必拍） | `ANCHOR_photo_opera` / `_bridge` / `_bluehour` | 无 | 蓝调时分只在蓝调时段算 |

“要先完成的行动”的名字是暂定的，写任务系统时对上就行（改 presets 文件里的 `action`）。

#### 在 Blender 里放打卡点
1. 在要拍的东西那里加一个**空物体**（Add → Empty → Plain Axes），名字改成上表的点位名，比如 `ANCHOR_photo_hiyori`。
2. **推荐**：把要拍的模型（店面、长椅）拖成这个空物体的子物体。这样判定按模型的实际大小算，最准。
3. 不想动层级也行：只放空物体，代码就把它当成一个球，球的大小按 presets 里的 `radius`（米）算。放在要拍的东西的中心。
4. 想单独调某个点，可以在空物体上加自定义属性：`radius`、`minCoverage`、`label`。glTF 导出时勾选 Custom Properties，代码会读到。
5. Blender 复制出来的 `ANCHOR_photo_hiyori.001` 也认得。找不到的点会在浏览器控制台提示“找不到打卡点……先跳过”，不会报错。
6. 如果场景是用 `anchors.json` 交付的，就把它传给 `setupTokyo(photo, { anchors: json })`。
   - 支持 `photo_spot: [{ id, target }]`、`{ "ANCHOR_photo_xxx": [x, y, z] }` 几种写法。
   - 坐标还是 Blender 的，就加 `coords: 'blender'`，代码会自动换成 (x, z, −y)。

#### 改打卡点的名字、位置、数量
全部在 `presets/tokyo.js` / `presets/sydney.js` 的 `spotDefs` 里，一个打卡点一段：

| 想改什么 | 改哪个字段 |
|---|---|
| 名字（取景框和章上显示） | `label`（章上想写别的就加 `stampLabel`） |
| 位置 | 在 Blender 里挪空物体；点位名对应 `anchor` |
| 太远也算 / 太近才算 | `minCoverage`（占画面比例，0.04 = 4%） |
| 凑近拍局部算不算 | `minVisible`（主体至少露出多少，默认 0.5） |
| 只在某个时段算 | `phases: ['sunset']` |
| 镜头要朝某个方向 | `facing` |
| 某个东西要一起入画 | `also: ['sy_opera']` |
| 取景框里的小字 | `tip`（时段不对时显示 `waitTip`） |
| 章中间的图案 | `icon`（`stamps.js` 里的 ICONS） |
| 去掉一个点 | 删掉那一段 |
| 只开必拍的点 | `setupTokyo(photo, { include: (d) => d.required })` |

回忆卡的标题、副标题、底下一行字在同一文件的 `card` 里。

#### 纪念章
`src/photo/stamps.js` 用 Canvas 程序画，全部是虚构图案，不是任何真章或品牌：
- 东京：车站纪念章的样子。圆形双圈、上沿一圈小字、中间线描、下面一条站名带。
- 悉尼：海岸步道标记牌的样子。圆角牌子、编号、线描、波浪线和箭头。

两城都用朱红印泥，带随机的斑驳和白点。同一个打卡点每次画出来都一样。

### 人物进照片（自拍、合影、先问一声）
四个 3D 人物（凛、林川、Camille、Noah）还没接进网页，下面这些接口和具体模型无关，模型接上后直接用。测试页里用“胶囊 + 球形头”的占位人形演示。

**宿主要传的东西**（`setupTokyo` / `setupSydney` 的参数）：
```js
setupSydney(photo, {
  getPhase: () => 当前时段,
  avatar: 玩家人物,                 // Object3D；取景时自动藏起来，退出时恢复
  people: { maya: mayaModel },     // 可选：按 id 直接给人物模型；不给就按 presets 里写的名字（如 NPC_maya）在场景里找
});
photo.setConsent('maya');          // 剧情里问过“可以拍吗”、对方答应后调用
```
各城可能入镜的人写在 presets 的 `people` 里（东京：凛、林川、路过的人；悉尼：Noah、Maya、Camille），都是预览提案，改那里就行。

**1. 定时自拍（Noah 线的核心：“拍照的人也在照片里”）**
- 取景时按 **T**：相机留在原地（像放上了三脚架），焦段、横竖、低角度都锁住，屏幕一直显示三脚架上的画面。
- 10 秒倒数：取景框右上角一盏红色指示灯闪（最后 3 秒闪得快）和数字。再按 T 或 Esc 取消。
- 人物从相机旁边走进画面，站到**画面里人少那一侧的三分线上**（不挡同伴、不挡中间的景），面向相机；剩 3 秒时摆姿势。
- 宿主听这几个事件让人物动起来：

  | 事件 | 宿主做什么 |
  |---|---|
  | `selftimer:start`（`standAt` 建议站位、`lookAt` 相机位置） | 让人物走到 `standAt`、转身面向 `lookAt`；这段时间玩家可以自己挪人物 |
  | `selftimer:tick`（`remaining` 剩几秒） | 剩 3 秒时播放 `pose_photo` |
  | `selftimer:fire` | 快门这一刻（还没摆好就立刻摆好） |
  | `selftimer:end`（`record` 照片） / `selftimer:cancel` | 把镜头和控制还给玩家 |
- 照片元信息记 `selfie: true`。悉尼回忆卡里有自拍时，那行字写“这次，我也在照片里”。
- `new PhotoSystem({ selfTimer: { view: 'host' } })`：倒数时屏幕交还宿主自己的镜头（比如第三人称跟着人物），只在角上显示倒数。默认 `'tripod'`。

**2. 谁被拍进了照片**
- 和打卡点同一套判断：在画面里、没被挡住、占画面 ≥0.3%、至少一半露在画面里。人被别人挡住也算挡住。
- 照片元信息：`subjects: ['noah', 'maya']`，`subjectsInFrame: [{ id, label, coverage, needsConsent, consent }]`。剧情可以据此判断“合影里有没有拍到某人”。
- 打卡点可以要求某人入镜：悉尼咖啡店写了 `needSubjects: ['maya']`，合影里没有 Maya 就不盖章，派发 `subjectwait`。
- 站在地标前面的人不算“挡住地标”，所以自拍、合影也能盖地标的章。

**3. 拍人前先问一声**（Maya 的合影、东京录“谢谢”的路人）
- `people` 里标 `needsConsent: true` 的人，没问过就出现在画面里时，取景框上方夹一张纸条“先问一声，可以拍吗？”，下面写名字；打卡点的框不变朱红，提示“问过 Maya 再拍，才算数”。
- 照片照样能拍、照样留在相册，但元信息 `storyOk: false`、`consentMissing: ['maya']`，不盖章，派发 `consentwait`。

**4. 取景时藏起自己**：进入取景把 `avatar` 设成不可见（第三人称镜头下人物会挡住画面），退出时恢复原样；定时自拍时例外。

**人物模型接入时宿主要做的几步：**
1. 队友的模型（现在是 zip/blend，在分支 `codex/library-character-5060` 的 `projects/cijian-5060-models/character/`）在 Blender 里导出成 GLB，带骨骼和三个动作：`idle`（站着）、`walk`（走）、`pose_photo`（拍照姿势）。人物正面朝 Blender 的 −Y（导出后是 three 的 +Z），脚底在原点，单位米。
2. NPC 在场景里的物体名用 `NPC_linchuan`、`NPC_maya` 这种（和 presets 的 `node` 对上）；或者加载后用 `people: { maya: 模型 }` 直接传。
3. 玩家人物传给 `avatar`。
4. 在 `selftimer:*` 事件里用 `AnimationMixer` 切动作、移动人物（测试页 `src/photo-test.js` 里“定时自拍”那段就是照着做的，换成真模型只要把 `person.play('walk')` 换成播放对应动画）。
5. 人物身上的包围盒会被用来算占比：如果模型带了很大的不可见物体（比如碰撞胶囊），给它设 `visible = false` 或单独放，不要挂在人物下面。

### 按我们的场景设计的取景功能
看过三台电脑的渲染（谷中窄街逆光、电线杆、五重塔和雷门大提灯、5060 的店面细节、悉尼远眺）后加的：

| 功能 | 为什么 | 操作 |
|---|---|---|
| 竖拍 | 五重塔、大提灯、电线杆、台阶都是竖向的主体 | R（方画幅的即时成像不分横竖） |
| 曝光补偿 ±2 EV（1/3 档） | 谷中主机位是对着低太阳逆光拍；悉尼有蓝调夜景 | ↑↓ 或 Shift+滚轮；在管线的色调映射之前生效，高光不会发灰 |
| 低角度 | 路面字、仰拍塔檐和提灯（参考 tokyo-fill 的 q_ground、q_pagoda 机位） | V，相机放低 0.7 米，不改宿主的人物位置 |
| 每城不同焦段 | 东京街宽只有几米，要 24mm；悉尼隔着海看歌剧院和大桥，要 135mm | `focalLengths` / `setFocalLengths()` |
| 构图提示 | 拍到打卡点时取景框四角变暖、框内出现地点名，玩家知道这张会盖章 | 自动；按快门时才做遮挡判定 |
| 定时自拍 | Noah 线“拍照的人也在照片里” | T |

照片元信息里会记下 `ev`、`orientation`（landscape / portrait / square）、`lowAngle`。

### 照片元信息
`{ id, createdOrder, createdAt, sceneId, spotId, spotHits, selfie, subjects, subjectsInFrame, consentMissing, storyOk, phase, weather, cameraStyle, ev, orientation, lowAngle, camera: { position, quaternion, focalMm } }`
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
| `stamps.js` | 纪念章（程序画的虚构图案） |
| `presets/` | 东京、悉尼的配置和 `setupCity`、`resolveSpots`、`applyPhase` |

## 测试页
```bash
cd projects/cijian-app && python3 -m http.server 8766
```
打开 http://127.0.0.1:8766/photo-test.html （改过代码后用 Cmd+Shift+R 强制刷新，否则浏览器会用旧文件）。
- `?city=tokyo`（默认）：一条小街，摆着三家店、台阶、门和大提灯、五重塔、电线杆。
- `?city=sydney`：北岸步道远眺海港，摆着咖啡店、望远镜地标、长椅、剧院和大桥示意。距离按真实大致比例。悉尼默认用 `?pipeline=composer`。

场景是程序生成的占位几何（`src/test-scenes/`），只用来测拍照，不是正式美术。店名、招牌都是虚构的。
左上角能切城市、切时段、换相机，打卡点列表里每个点有“去这里”按钮：跳到参考机位，并设好建议的焦段、横竖、低角度。
“剧情行动已完成”勾掉后，可以测“先录音、后盖章”。
“人物”一栏：定时自拍按钮（或取景时按 T）、“已经问过可以拍吗”开关；“上一张”显示入镜的人。
测试页是第一人称，玩家人物就站在镜头的位置（从里面看不见自己的模型）；定时自拍结束后，镜头回到人物站的地方、看向刚才放相机的位置。
浏览器面板在后台时动画会停，可以在控制台用 `setInterval(frame, 60)` 手动推帧。
Three.js r170 和后期扩展放在本目录 `vendor/`（`three.module.js` 来自 yuyake-dandan，`addons/postprocessing`、`addons/shaders` 来自 sydney-harbour，MIT），不依赖网络。
`?pipeline=composer` 用悉尼同款管线测试。

测试页默认用 `HdrPipeline`，查找表从 `test-data/lut_morning.bin`、`test-data/lut_sunset.bin` 读：
就是 `projects/cijian-5070/web/data/` 里的同名文件（Git LFS），复制过来即可，`test-data/` 不入库。
没有这两个文件时自动退回 `StandardPipeline`；`?pipeline=standard` 可强制用后者。

## 已验证（2026-11-03，Mac M2，Claude 应用内置浏览器）
东京、悉尼两套配置的两轮审改见 `REVIEW_ROUNDS.md`。要点：
- **14 个打卡点都能在参考机位盖章。** 凑近只拍到一角、背对、太远、被挡、时段不对的都不算。
- **照片和取景时颜色一致**：块平均差最大值东京白天、日落 ≤1.6/255，悉尼白天、黄金时段 ≤1.8/255。为此改成拍照时泛光按取景框的像素高度算。
- **悉尼焦段**：在步道上拍约 1 公里外的歌剧院，85mm 以上才够 4%。
- **竖拍和低角度**：胶片旁轴竖拍、24mm、低角度拍出 2000×3000，元信息正确。
- **纪念章和回忆卡**：两城纪念章、带章的回忆卡（1—7 枚）都存成文件看过。

人物进照片（第三、四轮，见 `REVIEW_ROUNDS.md`）：
- **定时自拍**：东京台阶顶日落、悉尼咖啡店、悉尼海边黄金时段三处真拍，人物走到三分线、面向相机、摆姿势，照片 `selfie: true`、`subjects` 正确，同时盖了台阶 / 海边的章。
- **人少的一侧**：林川在画面右边时人物站左三分线（画面坐标 −0.31），林川在左边时站右三分线（+0.31）。
- **先问一声**：没问过 Maya 拍咖啡店，照片留下、不盖章、`storyOk: false`；问过之后盖章。没问过时框不变朱红，纸条和提示都出现。
- **合影要有 Maya**：自拍时人物挡住了 Maya，判定为 Maya 不在画面里，派发 `subjectwait`，不盖章。
- **藏起自己**：进取景人物不可见、退出恢复；定时中可见。

以下是之前（东京/悉尼配置之前）的验证：
- **悉尼同款管线（EffectComposer + UnrealBloom + ACES）**：照片和屏幕逐块比较，白天平均差 0.13/255、最大 1.15/255，日落最大 0.46/255；拍完 composer 恢复原尺寸。
- 竖拍（2000×3000）、低角度、曝光补偿都在真拍的照片里生效，元信息正确；一次拍照约 0.3—0.4 秒。
- **照片和屏幕颜色一致**：关掉相机风格后，同一机位 2048×1536（屏幕）和 3000×2250（照片）逐块比较（8×8 区块），白天最大差 0.23/255，日落（有泛光）最大差 0.52/255。为此把泛光链改成始终按屏幕分辨率起步，否则照片的泛光会偏小（差约 5/255）。
- 取景框比例、焦段视角和拍出的照片一致；`hideInPhoto` 的物体不进照片。
- 打卡判定四种情况都对：正对 ✓、背对 ✗、太远（占 0.6%）✗、被房子挡住 ✗；真拍时 `spotHits` 正确。
- 即时成像 3000×3000、胶片旁轴 3000×2000 的 JPEG，冲印版和回忆卡 PNG 存成文件后打开正常。
- 一次拍照从按快门到存好约 0.8 秒，显影小图 0.4 秒内出现。

**没验证：**
- 没接真实东京、悉尼场景（东京烘焙包约 477MB，本机磁盘和网络都不够）。
  - 两条管线的数学和原工程一致，取景功能按渲染图设计，但相机风格是在测试小街上调的，接上真场景后要再看一眼。
  - 打卡点的门槛（`minCoverage`、`minVisible`、`radius`）是在占位几何上定的，接真模型后要在每个点拍一遍再调。
- 东京夕阳方向按 `game.js` 的 `LIGHT.sunset` 换算，没在真场景里对过。
- 悉尼三个时段的曝光、泛光数值是兜底值，没对过 sydney-harbour 的光照代码。
- 没在 5070 上测帧率。取景时每帧多两次全屏调色，预计影响很小。
- 内置浏览器不把下载存到磁盘，“点下载按钮 → 打开文件”要在 Chrome 里点一次确认。
- 人物部分只用占位人形测过：真模型的包围盒（头发、裙摆、手里的东西）会让占比偏大，`SUBJECT_MIN_COVERAGE` 和自拍站位距离（人占画面约一半高）要接上模型再看。
- 定时自拍的 `view: 'host'` 模式只确认了不画取景框、只显示倒数，没在第三人称镜头里实际玩过。
- 内置浏览器面板在后台，定时自拍的走路是手动推帧测的，没看过 60 帧下的流畅度。

## 临时的东西（之后要换）
- **打卡点**全部是预览提案，名字、数量、位置等用户拍板。
- **入镜人物**（`people`）、谁要先问、咖啡店合影要有 Maya，都是按剧情方案写的提案。
- 占位人形 `src/test-scenes/people.js` 只给测试页用。剧情行动的名字（`rec_bell` 等）是暂定的，要和任务系统对上。
- 集章存在 localStorage，正式版交给任务系统存档。
- `src/test-scenes/` 的占位场景、招牌和天空只给测试页用，不进正式游戏。
- 两台相机的调色数值：要拿东京烘焙场景再看一遍，满意后可以导出成 `.cube` 填进 `styles.js` 的 `lut`。
- 快门声是合成的占位声；中文字体用系统宋体兜底，正式版用思源宋体子集（`此间_相机.md` 3.5 节）。

## 还没做
景深和点击对焦、快门转场（切时段）、点照片回到现场、换相机菜单（现在用 `photo.setStyle()`）、书签地图页上盖章的动画。
