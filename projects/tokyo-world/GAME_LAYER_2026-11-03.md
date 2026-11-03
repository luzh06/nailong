# 此间 · 游戏层收尾交付（2026-11-03）

> 负责人：Claude（5070 本机，总装）。本文记录本轮新增的开场、第三人称人物与相机、NPC 互动、转场、拍照接入、图鉴、悉尼终章与回忆卡。
> 东京场景、碰撞、输入模块沿用 Codex / DeepSeek 已交付成果；`world.js` 只加了挂接点，渲染与碰撞实现未改。

## 怎么玩（给体验者）

1. 双击 `D:\project\chatgpt\ci\output\tokyo-three\打开此间.cmd`（或已运行的服务：<http://127.0.0.1:8780/web/index.html>）。用开启硬件加速的 Chrome / Edge。
2. 标题页「翻开这本书」→ 四张借阅卡选一位旅人（可换随身相机）→ 盖章出发 → 翻书镜头（可「跳过」）→ 入城后点一下画面开始。
3. 操作：WASD 行走（Shift 快走）· 鼠标环视 · 滚轮拉近拉远 · F 交谈 · C 举起相机、空格/单击快门、滚轮换焦段 · J 图鉴 · B 相册 · M 地图 · Esc 暂停。
4. 一局约 10–15 分钟：台阶拍「街区初见」→ 雷门前樱花树（凛/林川在此遇见对方）→ 宝蔵门前入夜、烟花（Camille/Noah 在此遇见对方）→ 图鉴里点「书页门」→ 悉尼书页章节 → 四人拼图回忆卡，可下载 PNG。

原展示模式仍可用：`index.html?classic`（机位选择 + 第一人称，与上一版一致）。
调试：`?role=rin|linchuan|camille|noah&skipintro` 跳过开场直接入城。

## 实际完成

| 模块 | 内容 | 文件 |
|---|---|---|
| 开场 | 3D 古书（5060 的 `cijian_antique_book.glb` 动画）+ 标题 + 借阅卡（四人立绘，Blender 渲染）+ 随身相机选择 + 翻书旁白 + 书页发光入城；开场期间城市后台加载并暂停渲染，未就绪时停在“书页正在显影”并显示真实进度 | `game/opening.mjs` |
| 人物 | 四人 OBJ（每个约 150 万面）→ 4 万面、2048 贴图 GLB，身高按角色缩放，软阴影。载入时自动绑骨：从网格横截面量取肩/腕/腿位置，建 17 根骨、按到骨段距离算蒙皮权重（小腿按就近分左右、去掉两鞋间的桥接三角），程序化步态驱动走/快走（步幅随速度）、站立呼吸、说话手势、转身内倾；有 `idle/walk/talk` 骨骼动画的 GLB 自动改用 AnimationMixer | `game/actors.mjs`、`game/skin.mjs`、`game/rig-preview.html`、`models/characters/*.glb`、`D:\project\cijian\tools\char_to_glb.py` |
| 相机 | 第三人称越肩跟随、滚轮 1.4–6 m、对真实碰撞三角面做相机避障（薄物体可穿过）、过场双人镜头；举起相机时切第一人称并隐藏自己 | `game/rig.mjs` |
| 拍照 | 接入 `app-photo` 分支的 PhotoSystem（取景框、焦段、快门、离屏 3000px、IndexedDB 相册、回忆卡）；照片管线与屏幕同一 AgX/泛光参数（含夜晚色调）；遮挡判定用 45 万面碰撞网格 | `game/photo/`、`game/render/pipeline.js` |
| NPC 互动 | 靠近出现「F 交谈」（触屏可点）；对白面板：逐字、立绘、三组选项（仅一组推进）、可告辞再来；同意后对方入镜才算互拍；对方用你的相机回拍一张（存入相册）；告别后对方沿小路离开渐隐 | `game/dialogue.mjs`、`game/main.mjs` |
| 剧情 | 单玩家 + 三 NPC；东京只遇见情侣对象（凛↔林川 樱花树下；Camille↔Noah 烟花处），另两人到悉尼海滩才首次认识；中国/巴黎为“此前旅程”预设已集齐 | `game/story-data.mjs` |
| 图鉴 | 古书样式；已显影条目显示插画 + 角上贴玩家实拍；东京 3/3 且互拍完成后出现「书页门」 | `game/journal.mjs` |
| 转场 | 快门叶片（入夜）、纸色幕布（书页门）、照片显影卡（每个图鉴点）、白光入城 | `game/fx.mjs` |
| 布景 | 程序生成樱花树（分枝、花云、花簇卡片、飘落花瓣、落花）；烟花（三种花型、HDR 进泛光、闪光提亮、合成闷响）；夜晚：曝光 −2.6 EV、蓝调色调、实时光与环境光调暗 | `game/sakura.mjs`、`game/fireworks.mjs` |
| 终章 | 悉尼三页插画（咖啡店 → 步道 → 海滩日落）→ 重逢对白 → 认识另两人 → 四块文化头像拼图合成回忆卡（移植团队《回忆卡》页面）→ 保存 PNG / 我的东京相册 / 再读一次 | `game/finale.mjs` |

`world.js` 改动（均为挂接点，默认值保持原行为）：`hooks`（camera/render/update/zoom/lookScale/blockMove/exit/obstacles/suspend）、`enterWalkAt/resumeWalk/setUiBlocked`、色调 `uGrade`、就绪事件 `cijian:ready`。
`index.html` 改标题并按 `?classic` 决定是否加载 `game/main.mjs`。`scripts/serve.py` 增加 `Cache-Control: no-cache`（更新后浏览器不再用旧脚本）。
同步到运行包：`node projects/tokyo-world/scripts/sync_game.mjs`（只复制游戏层相关文件并删除过期 .gz）。

## 验证（真实运行）

- 现有回归：碰撞/真实场景 18/18，`experience-controls` 18/18（Chrome）。
- 自动化完整通关（林川线，Playwright 有窗口 Chromium，真实时序）：TOKYO-01 → 相遇对白 → 同意互拍 → 互拍 + 回赠 → TOKYO-02 → 入夜 → TOKYO-03 → 书页门 → 终章 → 回忆卡按钮出现；相册 9 张；控制台 0 错误。
- Noah 线（烟花相遇 + 终章重逢/介绍对白）、凛线（樱花相遇、双人镜头）分别在内置浏览器走通并看图。
- 画面逐项看过截图：开场古书/借阅卡/翻书/入城、台阶第三人称、樱花树、夜晚宝蔵门 + 烟花、图鉴、终章拼图卡；手机 390×844 借阅卡排版。
- 性能：本轮能测到的只有 Intel Arc 140T 核显（Playwright 默认选中）：同一路线原展示模式 31.6 ms/帧，游戏模式 38.6 ms/帧；游戏层每帧 CPU 约 0.35 ms，差值主要来自第三人称视角看到更多街区。**RTX 5070 上尚未测**（上一版第一人称约 16.8 ms）。

## 已知边界（如实）

1. 人物骨骼为程序自动生成：走路、快走、站立、说话已流畅，但手指、裙摆、头发没有独立物理。Codex 交付手工绑骨动画后会自动替换（`TASK_CODEX_CHARACTERS.md`，现为可选优化）。
2. 樱花树是程序生成的风格化树；Codex 交付 `models/sakura.glb` 后需要我把 `createSakura({withTree:false})` + GLB 接上（约 10 行）。
3. 悉尼没有可行走场景：终章是图鉴插画 + 对白的“书页章节”，不冒充实景地图。
4. 夜晚是在日落光照上压暗 + 色调，不是重新烘焙的夜景；街区没有点灯。
5. 声音只有图鉴素材的翻书/快门/显影声、合成的风声和烟花声；没有城市背景音乐。
6. 触屏：摇杆/环视/交互提示/底部按钮可用；拍照快门依赖单击取景框，未在实体手机测试。
7. 打卡判定的阈值在真实场景各拍了一次，不同站位可能需要微调（`story-data.mjs` 的 `SPOTS`）。

地图问题清单见 `ISSUES_WALK_AUDIT_2026-11-03.md`（剧情路线全部可通行；8 项建模/材质问题已列坐标与截图）。

## 协作分工（按能力）

- **Codex**（建模强）：四人骨骼 + 动画、樱花树模型 → `TASK_CODEX_CHARACTERS.md`。
- **DeepSeek / DSH**（文字与测试 harness 扎实）：对白润色（只改字符串）+ 游戏流程 E2E 回归测试 → `TASK_DSH_DIALOGUE_AND_E2E.md`。
- **Claude**：总装、`game/` 全部代码、接入两人的交付并看图验收。

## 文件与 Git 状态

当前分支 `codex/tokyo-integration`，本轮没有提交、推送或合并。新增素材均来自团队仓库分支（`app-photo`、`codex/library-character-5060`）与桌面交付的《书本图鉴资产 v0.1》《回忆卡》页面；`vendor/SkeletonUtils.js` 为 three r170 原文件（MIT）。
