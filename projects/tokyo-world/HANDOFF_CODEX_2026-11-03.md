# Codex 交接：东京主场景、移动体验、真实地图与 DeepSeek 协作

> 本文保留接手前的历史快照。2026-11-03续做后的当前状态、路线实走与剩余边界，见 `FINAL_STATUS_2026-11-03.md`；下文“碰撞尚未接入/雷门断连”等已经修复，不要按旧状态重新实施。

更新时间：2026-11-03（Asia/Shanghai）。这是本轮实际状态快照，给新对话里的 Codex 直接续做。

## 0. 接手先读：目标、关键事实和立即动作

用户最新任务：完善已有东京主场景的模型构建、道路联通、第一人称移动、防穿墙、真实地图、操作 UI 和性能。必要时可以继续调用 Blender 建模，用户对成品质量要求很高。其他团队成员负责相机、开场、NPC 交互、剧情、转场和人物设置，本轮不要重做这些模块。

目前并未完成全部 bug 修复，不能把此前“可运行的最小整合版”当作最终成品。

**最重要的三个事实：**

1. **雷门到寺院参道仍未真正连通。** 旧导航不通；新生成导航也刚复测出不通。不要只补几个 null 后就宣布修复，必须同时核对可见地面、墙/栏杆和实际胶囊通行。
2. **真实碰撞已经做成独立代码和数据，但尚未接入运行中的 world.js。** 浏览器目前仍用旧的地面网格判断。控制器的 8 个合成回归测试通过，不代表真实街区已经防穿墙。
3. **真实地图已经接入运行网页并验证。** 它由实际模型三角面正投影生成；先前生图插画已经降为仅提供空白纸纹，不能当导航地图。

立即续做顺序：

- 先确认 DeepSeek 是否已经按 `DEEPSEEK_TASK.md` 在写输入组件，不碰他的独占文件。
- 读取本文件第 5—8 节，解决雷门地面/边界的真实断连。
- 把 `collision.mjs` 和新的碰撞/导航数据接到主循环；测试实际场景、道具、台阶与路口。
- 再接 DeepSeek 输入模块，统一 UI 状态；完成资源分区加载、真实进度和低画质档。
- 固定机位与实际行走验证，再处理白墙、硬接缝、模型岛边缘等画面问题。必要时使用 Blender 派生工程。

## 1. 用户意图与不可丢失的约束

### 1.1 当前范围

- 用户要求主场景能连续探索、不能穿墙、街区和寺院真正联通，操作自然，画面有较高审美。
- 原始规划是 **80×80 米核心区（6400 平方米）**。台阶、商店街西延和浅草寺实际已经超出核心区。必须如实区分核心区、扩展区和远景。
- 浅草寺是用户提出的虚构拼接；不能声称谷中与浅草寺的位置是真实地理。
- 谷中建筑/道路/地形尽量遵循现有 PLATEAU、OSM、DEM 数据。地图不能另造道路、楼群或高程。
- 用户明确允许继续用 Blender 修补/建模。保留原始来源，在可追溯的派生工程里做改动，不直接覆盖原 qs_h1/A/B/制作源。
- 不能把 UI 按钮出现、代码无语法错、或一条路线走几米，等同于整体体验验收完成。
- 旧交接要求每次模型质量改动做至少 5 轮“渲染→看图→记最差三个问题→改”。本轮没有完成新的 5 轮模型精修，切勿虚报。

### 1.2 明确留给其他人的模块

用户截图列明：相机模块、开场模块、NPC 互动、转场动效、人物设置由其他人开发，之后由用户再组装。
本轮只留接入口，不新增剧情/任务/相册/人物等系统。原有“保存照片”已经能用，应保持回归，但不扩成相机模块。

### 1.3 协作方式

用户原先有 SSH 远程协作者，后来明确说已经停掉，由本 Codex 接管。
用户现在要求 Codex 与他自己的 Claude Code / DeepSeek 分工，并要他自己复制提示词启动对方。
**不要擅自替用户启动第二个 DeepSeek 会话；先看对方的交接/文件状态。**

## 2. 工作目录、分支与来源

| 路径 | 用途 / 读写边界 |
|---|---|
| `D:\project\chatgpt\ci` | 本对话工作区，可写 |
| `D:\project\chatgpt\ci\nailong` | 仓库副本，本轮代码位置 |
| `...\nailong\projects\tokyo-world` | **本轮统一 Three.js 主场景源码** |
| `D:\project\chatgpt\ci\output\tokyo-three` | **当前可运行交付副本，含资产** |
| `D:\project\chatgpt\ci\output\tokyo-verification` | 浏览器验收、截图与 JSON |
| `D:\project\chatgpt\ci\tmp` | 本轮诊断/浏览器脚本与优化前副本 |
| `D:\Cijian\integ` | 已停止的 SSH 整合任务交接与成果，参考/只读源 |
| `D:\Cijian\pack` | 旧台阶段烘焙网页包，参考/只读源 |
| `D:\project\cijian\work` | 5070 建模源、最新 C/D/E/S/X、总装；保护原始资产 |
| `D:\project\cijian\nailong` | 原制作 Git 仓库，不要混淆当前副本 |

当前工作分支：`codex/tokyo-integration`。
当前 HEAD：`7eb997a169f28685b396c7e69ec778e617c52719`。
远端：`https://github.com/luzh06/nailong.git`。
**本轮 tokyo-world 新代码和改动尚未提交/推送。** 最早导入 5060 道具时存在 staged 内容，操作 Git 前先检查，不要 reset/revert 或随意全量提交。

Git 沙箱里 LFS filter 有时导致 `fatal: the remote end hung up unexpectedly`。只读状态可用：

```powershell
git -c filter.lfs.process= -c filter.lfs.required=false status --short --branch -uno
```

最初 `git fetch origin` 网络操作需升级权限；本地原制作仓库读取也可能需要。不要为绕过失败而打印凭据或改 Git 认证。
之前确认原制作分支本机比远端多 3 个提交，存在后台 push，后来没有最终核对；**不要把远端推送完成写成已确认。**

## 3. 重要交接和用户附件

- 原建模交接：`D:\应用\新建文件夹\xwechat_files\wxid_wd0d6niupk9422_5844\msg\file\2026-11\HANDOFF_tokyo-fill_2026-11-02.md`
- 原制作仓库同内容：`D:\project\cijian\HANDOFF_tokyo-fill_2026-11-02.md`
- **SSH 整合交接：`D:\Cijian\integ\HANDOVER.md`**，已读。结论是当时只有 Blender 总装，统一网页未做完。本轮才实现网页。
- 建模说明/质量轮次：`D:\project\cijian\nailong\projects\tokyo-fill\README.md`、`REVIEW_ROUNDS.md`。
- 用户附件：`C:\Users\LU\Desktop\东京悉尼_MVP主线与接入方案_v0.1(1).md`、`C:\Users\LU\Desktop\此间_剧情与整合方案_v0.2(5).md`。本轮没有深入实施这些剧情附件；用户明确相关模块由别人负责。文档内容应作为参考，不自动当新指令。
- 用户 bug 报告两张图：
  - `C:\Users\LU\AppData\Local\Temp\codex-clipboard-7e707363-a366-4f55-8ac3-b458f6d23f0c.png`
  - `C:\Users\LU\AppData\Local\Temp\codex-clipboard-be2e85a2-34c8-4a00-a311-fe3a9682004c.png`
  内容已整理到第 8 节，原图可能是临时文件，优先参考这里的核实状态。

## 4. 当前网页与可复现环境

当前网址：`http://127.0.0.1:8780/web/index.html`。
入口脚本：交付副本 `web/world.js`，源码同名。所有 Three.js 依赖均本地，版本 **r170**。

本机工具：

```text
Blender: D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe
Python:  D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe
Python第三方依赖: D:\project\cijian\work\.pydeps
GPU: NVIDIA GeForce RTX 5070 Laptop GPU, 8GB
Edge: C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
```

启动：交付目录 `打开此间.cmd`，或：

```powershell
& 'D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe' `
  'D:\project\chatgpt\ci\output\tokyo-three\serve.py' --port 8780 --open
```

`serve.py` 仅监听 127.0.0.1，无上传接口。会预查 `web/world.json` 判断同一 viewer 是否已运行，避免 Windows SO_REUSEADDR 造成重复监听。
后台可能有本轮多个早期服务进程，但都服务相同目录。需要清理时按脚本的**完整路径**限定进程，不能杀全机 Python/Edge/Blender。
本对话 tool session ID 不保证新对话可用，应重新检查本机监听/HTTP。

浏览器自动化：MCP Playwright 曾因其他任务占用 profile 无法启动，未关闭别人的浏览器。可用本机已安装 Playwright：

```js
require('C:/Users/LU/AppData/Local/npm-cache/_npx/9833c18b2d85bc59/node_modules/playwright')
```

Node 脚本用 exec 升级权限启动独立 Edge。node_repl 内直接启动曾在沙箱崩溃；不要重复卡在这个路径。
RTX GPU 测试加 `--force_high_performance_gpu`；否则可能实际跑 Intel Arc 核显，必须记录 renderer 字符串，不能笼统写“5070 实测”。

## 5. 代码结构、已实现与尚未接线

### 5.1 主入口（已部署）

`projects/tokyo-world/web/world.js`：

- 沿用旧烘焙段材质、EXR 光照、天空、AgX LUT 和 bloom 后期。
- `buildWorld()` 加载 `world.json` 的 A/B/C/D/E/S/X，共 7 层。
- A/B 空店面按预留位装配 5060 front/tent/goods 与小道具；共 **34 个 placements，18 种实际加载资产**。
- C/D/E 已有装修保留，避免和队友道具叠放；没有在源楼上开洞。
- 道具已有 LOD0/1/2，按 0/18/42 米切换，`_COL` 不渲染。
- 实时层使用共享纹理 cache、实时太阳阴影与同一雾/色调链。
- 旧 baked `far` 组隐藏，新 X 代替，不再加载旧远景卡片。
- 主街烘焙段止于 Blender y=-34，而 E 从 y=-62 接入；网页里放了 `viewer_street_bridge`，4.6×28.1 米、z=-.008 的实时路面补片。
- 路口 baked 模型使用 shader 世界坐标裁切，当前仍硬编码 x[-10.5,10.5]、Three z[20.1,28.7]，地面材质豁免。shader cache key 已区分裁切/地面，避免复用错误。
- `save photo` 用当前 frame()+canvas.toBlob，下载 PNG 无 HUD。保持即可，不扩为相机玩法。

当前仍有旧 `walk()`、`groundAt()`、`isWalkable()`，只读运行副本旧 `navigation.json`，**还没有真正调用 WalkWorld**。

### 5.2 本轮最新已部署的三项修复

1. `createMapUI` 已 import，创建后每帧 update(camera.position, direction, walking)。
2. 全图展开会停止行走、释放 pointer lock、清空键状态；M/Esc 缩放地图可用。
3. 全景俯瞰机位点击“进入行走”会明确提示先选地面机位，不再静默传回台阶。
4. `resize()` 按当前 pixelRatio 重设 HDR RT，更新 aspect 而不重设 FOV；用户滚轮视角保持。

最新源码与交付的 world.js 已复制一致。浏览器 headful smoke 已通过（第 10 节）。

### 5.3 真正碰撞与新地面数据（**源码完成，尚未部署/接入**）

源码：

- `web/collision.mjs`：`export class WalkWorld`，用官方 r170 Octree + Capsule。
- `web/vendor/Octree.js`、`Capsule.js`，从官方 r170 获取，仅把 import 改成本地路径；同目录 Three.js r170 用于 Node 测试。
- `scripts/gltf_geometry.py`：读取 GLB/glTF/bin，不载入贴图，遍历节点层级与 world transform，提供实际最终几何。
- `scripts/navigation.py`：用最终网页的 bk.glb + A–E + S + 道具 `_COL` 生成地面和简化碰撞。X/植物忽略。只处理派生数据，不保存源模型。
- `web/collision.bin`：**16,143,696 字节，448,436 三角面**。
- `web/collision-info.json`：逐资产统计（同名多实例的 sources 字典会覆盖计数，整体 triangles 才是总数）。
- `web/navigation.json`：0.25 米格，577×545，x0=-58、y0=-98；1,730,683 字节，158,047 个非 null 地面格。

**注意源码与交付的导航目前不同：**

- 运行副本 `output/tokyo-three/web/navigation.json` 还是旧 0.5 米格数据（约459KB）。
- 新的 0.25 米数据只在 source/web；没有无验证地覆盖运行网页。
- 新控制器单元测试全通过，但没有真实场景的大规模碰撞/性能验证。
- 448k 面再双面插入 Octree，会有启动和内存风险，必须测。必要时继续合并平面、按地面附近高度裁切、分区构建，不能牺牲墙/柱/栏杆的防穿效果。

WalkWorld API：

```js
const world = new WalkWorld(navigation, new Float32Array(collisionBuffer));
world.ground(x, blenderY); // 地面高度或 null
world.canStand(x, blenderY);
world.findSpawn(x, blenderY, maxDistance=3); // {x,y,height} 或 null
world.move({x,y,height}, dx, dy); // 修正后的位置，按 <=0.07m 子步避免穿薄墙
```

内部：玩家半径 .28m，脚到头约1.66m，最大跨台阶 .32m；碰撞模型采用实际 Three 坐标，控制器输入平面仍用 Blender x/y。
目前 `move` 遇缺地面/高差直接停止，没有完整落体；地面由精细网格控制，不是通用物理引擎。
正确接入方式：输入意图→速度*dt→WalkWorld.move→更新玩家/相机。不要同时保留两套移动写位置。

### 5.4 地图（已部署、已验证）

- `web/map-ui.mjs`、`map-ui.css`，已完成并接入 world.js。
- `web/map/actual-map.png`：1536×1536，186,175 字节。
- 实际底图来自 bk.glb+A–E+S 的顶面三角面正投影，包含真实建筑轮廓、道路、台阶、坡顶与地面高度层次；没有使用 bounding box 代替最终楼形。
- `scripts/map_reference.py` 可重建；`map/map-provenance.json` 保存输入路径、SHA、投影三角数。
- `web/map/yanaka-atlas.png` 是先前生图插画；**不能用作真实导航**。组件只从它取空白纸纹。
- 生图原始 prompt 存在 `web/map/imagegen-prompt.txt`；生成来源路径在本轮记录中。用户已明确不要造假，后续不得把插画楼形又当真实底图。

接口：

```js
const mapUI=createMapUI({container:document.body, mapBounds, onClose:()=>{}});
mapUI.update(camera.position, camera.getWorldDirection(tempVector), walking);
mapUI.toggle(); mapUI.dispose(); // expanded / element 可读
```

展开状态发 `document` 上 `cijian:mapchange`，`detail.expanded`。
M 展开/缩小，Esc 关全图，支持收起重开、手机布局、北向、20m比例尺、超界提示。
静态机位标记“当前视角”，行走标记“你在这里”，不会把俯瞰相机误说成玩家。

地图坐标边界：ENU east[-137,22]、north[-88,71]；不等于80×80正式核心区。
地图来源 SHA 记录生成时输入文件；之后 glTF 进行了法线/颜色量化，文件 SHA 改了，但 POSITION/UV 已验证完全不变。最终交付前可重建/刷新 provenance。

### 5.5 资源压缩（交付副本已应用；运行后还需整体测）

独立脚本：`scripts/optimize_delivery.py`。

- 17 张仍为32bit的 EXR → HALF+ZIP：189,029,263 → 40,919,663 字节，减少148.1MB。
- 逐张重载验证，最大绝对误差0.0009765625，符合half精度。
- 31个模型bin：297,731,044 → 253,465,492 字节，减少44.3MB。
- 只量化 NORMAL / COLOR / 可容纳索引，POSITION和UV逐accessor验证完全一致。
- 标准 `KHR_mesh_quantization`，不需要decoder；现有 r170 GLTFLoader 支持路径已在最新网页smoke中跑过。
- 所有glTF外部引用验证缺失0。
- `web/asset-manifest.json` 在交付副本：437项引用，`totalBytes=466842715`。
- `optimization-exr.json`、`optimization-models.json`、`optimization-gzip.json` 在交付根目录。
- 备份：`D:\project\chatgpt\ci\tmp\tokyo-optimization-backup\`。
- `.gz` sidecar 已生成，候选传输量268,695,564字节；**serve.py未启用gzip，不能把268.7MB写成当前首屏实际传输量。** world.js后续已改，部分.gz会过期，启用前必须重建并检测。
- 分区延迟加载、按字节进度、低画质档尚未实现；目前仍一次性等待所有主要图层。

## 6. 坐标约定：接线前必须保持一致

```text
ENU (E,N,z) → Blender:
  x = 1.8 - N
  y = E + 32.5
  z = 高度

Blender (x,y,z) → Three.js:
  (x,z,-y)

Three.js → ENU:
  E = -three.z - 32.5
  N = 1.8 - three.x
```

- GLB/glTF 已经在导出时转换为 Y-up，加载模型后不能再整体旋转一次。
- A/B anchors 同时有 `center_qs_h1`、`outward_qs_h1` 与 ENU 字段。
- C/D/E meta 的 `center_enu` 是 ENU；旧交接笼统说“已是世界系”容易误导，不能直接当Three坐标。
- 5060道具原点在墙线，Blender本地 -Y 朝街。放置旋转：`atan2(outwardModelY,outwardModelX)+PI/2`，在 Three 绕Y旋转。
- 新导航和旧导航都是 Blender x/y 平面，`groundAt(camera.x,-camera.z)`。

## 7. 联通性核查：明确仍失败的位置

诊断脚本：`D:\project\chatgpt\ci\tmp\check-nav-connectivity.py`。
它做4邻接、相邻高度差<=.42的地面洪泛，**不包含胶囊碰撞/半径**，只能证明必要条件。

2026-11-03 对新源码导航的实际输出：

| 点 | Blender 平面 x,y | 新导航高度 | 与台阶连通 |
|---|---|---:|---|
| stairs | 1.2,15.2 | 4.293 | 是 |
| west_street | -2.2,-88.5 | -0.320 | 是 |
| junction | 2.1,-25.7 | -0.320 | 是 |
| north_lane | -25.4,-19.5 | 0.546 | 是 |
| gate（雷门外机位） | 29.3,-8 | 1.101 | 是 |
| court（宝蔵门/参道机位） | 50.2,-10.1 | 1.005 | **否** |

起点连通格121,438 / 有效格158,047。
旧导航的参道独立条带在 x≈42.5…83.5、y≈-12.5…-6.5，约1079格；x≈42有0.5米null缝，实测雷门方向走到x41.54就停。
**新导航也未自动解决。** 应在 Blender/实际几何核查 D停车场/通路与 S_ground、S_site 的边缘、入口台阶/栏杆，做可见、合理且不侵占真实楼的衔接。不能只扩大导航数值或让玩家跨空隙。

## 8. 用户 bug 清单与真实处理状态

| 编号 | 问题 | 当前状态 / 下一步 |
|---|---|---|
| 1 | 雷门走不过去，参道死角 | **仍未修完**；第7节有新旧数据复现 |
| 2 | 俯瞰进入行走静默传送、角度/下拉不一致 | 已加俯瞰禁止进入行走并明确提示，最新smoke通过；普通行走状态仍待统一接线 |
| 3 | 手机/平板没有移动方式 | 分给外部DeepSeek输入模块，当前尚未交付/接入 |
| 4 | 道具无碰撞、镜头点形状、近墙穿透 | 新胶囊+实际道具_COL数据已做，**尚未接运行主循环** |
| 5 | 走进布景、边缘/无形墙突兀 | 新导航有限定详细区边界但尚未部署；需要实走+可见边界/布局处理 |
| 6 | 退出行走后底部提示不恢复 | 地图展开/关闭提示已处理；全局输入/模式由DeepSeek模块+父接线统一 |
| 7 | 首屏647MB/全量加载、缺低档、进度99%停住 | 压缩到引用约466.8MB；分区加载/按字节进度/低档仍待做 |
| 8 | web目录不自包含 | 当前设计是整个tokyo-three根目录部署，README说明；只上传web会缺bake/assets，不能误称单web可部署 |
| 9 | addCards没接，背景模型岛/白块 | 旧卡片是有意用X替换，别机械重开卡片；模型岛边缘/近处白块问题仍需实际美术处理；unused函数可清理 |
| 10 | morning HDR不存在、死光照代码 | 当前MAN仅sunset，不触发；未来要删死配置或补足资源，不能开放按钮后404 |
| 11 | shader discard硬编码裁切箱 | 当前仍在，且只对旧baked材质；建议配置化或派生baked模型精确删面。不要拿它当通用“开洞” |
| 12 | 精细模式resize丢HDR倍率、重置FOV | **已修复并smoke通过**；低档/MSAA可调还没做 |
| 13a | ShiftRight不加速 | 待DeepSeek输入模块 |
| 13b | defines=undefined警告 | `fsPass`仍传可选undefined，尚未清理；不影响已测画面但要修 |
| 13c | ?bench/?shots残留且post为空 | 仍有死调试路径，成品入口应清理或迁移独立工具 |

## 9. Codex / 外部 DeepSeek 文件所有权（避免互相干扰）

给用户的完整任务书：`projects/tokyo-world/DEEPSEEK_TASK.md`。
用户要自己复制给 Claude Code；截至本交接，没有代他启动 DeepSeek CLI，也未拿到对方新交付。
已只读确认本机 Claude Code 配置指向 `https://api.deepseek.com/anthropic`，模型字段 `deepseek-flash`。**没有读取或输出认证Token内容。**

### DeepSeek 独占

- `web/experience-controls.mjs`
- `web/experience-controls.css`
- `tests/experience-controls.test.cjs`
- `tests/experience-controls-harness.html`
- `CONTROLS_HANDOFF.md`

### Codex 独占

world.js、index.html、collision.mjs、导航/碰撞数据、地图/地图UI、场景模型和纹理/烘焙、资源清单/压缩、serve.py、打包与最终集成。
双方不切共享分支、不合并/推送、不撤销对方编辑。DeepSeek只读world.js，最终由Codex替换旧输入监听器接线。

固定接口：

```js
const controls=createExperienceControls({
 canvas,container:document.body,
 onLook:({dx,dy,source})=>{},
 onZoom:({deltaY,source})=>{},
 onExit:({reason})=>{},
 onHint:text=>{}
});
controls.setMode('view'); // view | walk | blocked
controls.getMoveIntent(); // {forward:-1..1,right:-1..1,sprint:boolean}
controls.reset(); controls.dispose();
```

DeepSeek不直接改相机/玩家坐标，不做碰撞，不读导航；Codex每帧读取意图后调用WalkWorld。
UI地图展开时进入blocked，关闭后由宿主恢复；父端必须统一清按键、释放锁、更新按钮和提示。

本轮内部子代理已完成并停下：

- map_ui：真实地图与独立组件，结果见5.4。
- asset_performance：EXR/几何量化/资源清单，结果见5.5。
- review_three_integration：只读审查，最近已认可地图/aerial/resize三项新改动；没有替真实碰撞背书。

## 10. 已执行验证与证据，别扩大结论

### 10.1 旧整合版本浏览器验证

`output/tokyo-verification/report.json`，以及交付根 `verification.json`：

- Edge有窗口，RTX5070，1440×900。
- 7个图层，34道具；7机位出图；照片PNG打开非黑且无HUD。
- 测试约5秒，主机位平均帧18.272ms（约54.7FPS），UI约60FPS。
- WASD移动2.287米；errors=0，failed requests=0。
- 这是旧集成测试，不是“全地图60FPS”，也不是“碰撞已验证”。

### 10.2 最新地图/俯瞰/resize smoke（资源压缩后）

脚本：`tmp/check-world-map-handoff.cjs`。
报告：`output/tokyo-verification/handoff-smoke.json`。
截图：`output/tokyo-verification/integrated-map.png`。

实测：errors=[]、mapLoaded=true、M展开=true、Esc收起=true、aerialStable=true、resizePreservedFov=true。
1100×700、pixelRatio1.5时canvas1650×1050，FOV保留43.7791135398。
源码node --check通过。最新三项改动已让 code-reviewer 复查，无新高置信缺陷。

### 10.3 碰撞回归测试（仅合成几何）

```powershell
node --test projects/tokyo-world/tests/collision.test.mjs
```

8/8通过：控制器存在、快移不穿薄墙、贴墙滑动、门洞可过/墙不可过、墙双向阻挡、缺地面与高台阶阻挡、小台阶可上、出生点不嵌墙。
**未覆盖实际448k面碰撞树的构建时间、内存、所有真实门洞、全路线。**

### 10.4 地图子代理验证

独立浏览器1440×900/390×844、M/Esc、收起重开、位置/方向和边界，pageerror0。
截图在项目或workspace输出中以 `map-compact.png`、`map-expanded.png`、`map-mobile.png` 命名，可用rg定位，勿误当主场景移动测试。

## 11. 接手后的可执行顺序与验收门槛

### P0：完成真正移动与联通

1. 查询DeepSeek交付，保持所有权边界。
2. 先测源码新WalkWorld在真实collision.bin上的构建耗时/内存、几个合法出生点。
3. 修复雷门断连：查实际地面边缘、门洞净宽、栏杆、地形高差；需要时用Blender派生衔接几何。地面补片必须可见、合理，不能只改nav作弊。
4. 接主循环。替换旧isWalkable逻辑，不能两套移动同时写坐标。合法地面机位进入行走使用findSpawn，附近找不到就明确提示，不默默传送到台阶。
5. 场景边缘布置合理可见的边界/路线，阻止进入无纹理布景，别只设突然撞上的无形墙。
6. 实际连续路线至少：台阶↔主街西端；路口↔北巷；路口↔南侧/停车场↔雷门门洞↔参道↔宝蔵门。往返均测。
7. 对准墙面、斜墙、拐角、围栏、门柱、贩卖机、外机、货架走/快走，不能穿透；坡面与台阶贴地，不掉空、不漂浮。

### P1：统一输入/界面状态

- 接DeepSeek模块前读CONTROLS_HANDOFF，删除父旧键鼠监听器，避免重复移动/双重旋转。
- 支持ShiftRight；退出/失焦/地图展开/切机位清理输入。
- 移动与地图标记持续同步；触屏双指移动+环视、pointercancel、blocked模式验证。
- 避免地图与摇杆重叠：地图右下，摇杆左下，帮助与状态简明。
- 相机/开场/NPC等接口留给别人，不能越界扩写。

### P2：加载、性能与视觉

- 利用asset-manifest实现按字节、URL去重进度。分阶段加载核心/邻近街区，道具和远景延后，切机位保证等待目标区就绪。
- 做真实低/标准/精细档，调整分辨率、MSAA、阴影、bloom成本；不能只有DPR切换。
- 可用gzip sidecar但先重建并启用安全的Accept-Encoding/Vary处理；当前268.7MB只是潜在gzip量。
- 清理死morning、addCards、bench/shots/post分支与警告，保留独立测试脚本。
- Blender精修派生道路/地块缝、白墙/重复装饰、背景边缘。固定主机位不能变差；做渲染看图与最差三问题记录。

### 完成主场景的判定

- 上述关键路线真实步行往返全部通过，且不会穿墙/道具或进入布景。
- 地图严格对应当前模型和当前位置，俯瞰/静态视角标注准确。
- 新开网页、刷新、切机位、开关地图、触屏/键鼠状态一致。
- RTX5070有窗口测试，另有低档测试，记录真实renderer/分辨率/路线/采样长度，不泛化单点性能。
- 抽查下载照片、全部资产请求、控制台错误与警告。
- 合并main/公开发布另遵守用户确认边界，当前不擅自merge/push。

## 12. 常用命令与重新生成风险

### 安全验证

```powershell
Set-Location D:\project\chatgpt\ci\nailong
node --check projects/tokyo-world/web/world.js
node --test projects/tokyo-world/tests/collision.test.mjs
```

### 重建碰撞/导航（只写指定source/web，当前正确参数）

```powershell
& 'D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe' -b --factory-startup --python-exit-code 1 `
  -P 'D:\project\chatgpt\ci\nailong\projects\tokyo-world\scripts\navigation.py' -- `
  --package 'D:\project\chatgpt\ci\output\tokyo-three' `
  --out 'D:\project\chatgpt\ci\nailong\projects\tokyo-world\web'
```

**旧README里从ig_v2.blend生成navigation的命令已经过时，需修正文档，别直接照跑。**

### 联通性诊断

```powershell
& 'D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe' `
  'D:\project\chatgpt\ci\tmp\check-nav-connectivity.py' `
  'D:\project\chatgpt\ci\nailong\projects\tokyo-world\web\navigation.json'
```

### 打包风险

- `scripts/prepare.py` 会从旧pack/原始GLB重新复制、转换，可能覆盖已经HALF压缩/量化的交付副本，令体积回涨。**不要在未做备份和确认流水线顺序时直接重跑。**
- `resize_baked.py` 是早期1K缩图脚本；后来 optimize_delivery.py 才做HALF+ZIP。当前优化后副本是权威运行资源。
- 同步主脚本或地图后，asset-manifest/.gz会变旧，最终应重生成；当前world.js已在manifest生成后改变，字节数需刷新。
- 新nav/collision没有复制运行副本是有意的验证隔离，不是丢文件。
- 当前 source/web 不是完整资产目录；output/tokyo-three 才能完整运行。不要只起source/web然后误判404为模型损坏。

## 13. 已核对的开源参考与用法边界

- Three.js r170官方FPS： https://github.com/mrdoob/three.js/blob/r170/examples/games_fps.html
  参考Capsule/Octree与输入、碰撞分离；已使用同版本官方Octree/Capsule文件。
- Rapier角色控制： https://rapier.rs/docs/user_guides/javascript/character_controller/
  参考move-and-slide、autostep、snap-to-ground验收规则。目前没有替换成Rapier，别为了引用示例顺手引入新物理栈。
- NippleJS： https://github.com/yoannmoinet/nipplejs
  DeepSeek参考触屏摇杆/多指交互；可以用原生PointerEvents实现，避免无必要依赖。
- Sketchbook： https://github.com/swift502/Sketchbook
  项目已归档，只参考输入/角色状态分离，不整包移植cannon/其他栈。

使用开源代码要保留许可和出处。当前交付 `licenses/` 有素材表和THIRD_PARTY_NOTICES，新增Octree/Capsule相关许可最终应核对登记。

## 14. 给新对话的一句话启动方式

“请先完整读取 `D:\project\chatgpt\ci\nailong\projects\tokyo-world\HANDOFF_CODEX_2026-11-03.md`，继续东京主场景工作。优先完成真实碰撞接线和雷门往返通路，严格避开DeepSeek输入模块所有权。用户允许必要时继续用Blender建模，质量要求高；地图不得造假；其他剧情/相机/NPC模块由别人负责。先核对已完成内容，不要重新从零整合。”
