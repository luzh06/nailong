# 给 Codex 的任务：四位主角骨骼动画 + 樱花树（2026-11-03）

> 发起：Claude（本轮总装负责人）。你只做建模/骨骼/动画，**不要改 `web/` 下的任何 .js/.mjs/.html/.css**，网页接线由 Claude 负责。
> 交付后在本文件末尾追加「交付记录」一节即可，Claude 会接入并看图验收。

## 现状

`web/models/characters/{rin,linchuan,camille,noah}.glb` 已由 Claude 从 5060 分支的四个 OBJ 转出（`D:\project\cijian\tools\char_to_glb.py`）：
静态网格、4 万三角面、贴图 2048/1024、脚底在原点、身高统一 1.70 m、正面朝 three 的 +Z（Blender −Y）、**没有骨骼**。
网页当前用程序化摆动（呼吸、走路颠簸）临时顶替，能看但腿不会动。原始 OBJ：`D:\project\cijian\_inbox\character\obj\c1..c4`
（c1=Camille，c2=林川，c3=Noah，c4=凛），预览图 `web/models/characters/_preview.png`。

## 任务 1（最重要）：给四人做骨骼和动画

对 `web/models/characters/*.glb` 逐个：

1. 绑定人形骨骼（Rigify 基础人形或自建 ~20 骨即可；自动权重失败时可先体素重网格化一个低模代理再传递权重）。
2. 做三个循环/单次动画，**名字必须一致**：
   - `idle`：站立呼吸，2–4 秒循环，手臂自然下垂（不要 T-pose）。
   - `walk`：步行循环，约 1.1 秒一步周期，**原地**（根骨不前进，网页负责位移），步幅按 1.8 m/s 设计。
   - `talk`：站立交谈，轻微手势/点头，3–4 秒循环。
   - 可选 `wave`（挥手，单次）、`pose_photo`（举相机拍照姿势，单次停住）。
3. 保持：脚底在原点、正面 three +Z、单位米、身高 1.70 m（网页会按角色再缩放）、三角面 ≤ 45k、贴图 ≤ 2048。
4. 导出 GLB 覆盖原文件（先备份为 `*.static.glb`），在 three r170 `GLTFLoader` 能读出 `gltf.animations` 中上述名字。

验收：Blender 渲一张 idle/walk 中间帧四人并排图放 `web/models/characters/_rigged_preview.png`；面数、文件大小、动画名列表写进交付记录。
网页端不需要改：Claude 的代码会自动检测 `gltf.animations` 有 `idle/walk/talk` 就用 AnimationMixer，没有就退回程序化摆动。

## 任务 2：樱花树 `web/models/sakura.glb`

剧情 TOKYO-02「樱花树下」需要一棵能近看的樱花树（当前网页里是 Claude 程序生成的临时树）。

- 高约 6–7 m，树冠直径约 6 m；树干/主枝有树皮纹理，花冠用卡片簇（alpha 剪裁），粉白偏暖。
- ≤ 60k 三角面，贴图 ≤ 2048，原点在树根中心、+Y 向上。
- 不需要碰撞体（网页用圆柱碰撞）；树下留出 ≥ 3 m 半径的可站立空地。
- CC0 贴图可用（Poly Haven / ambientCG），在 `licenses/` 里登记来源。

## 不要做

- 不要改 `world.js`、`index.html`、`game/` 目录、`experience-controls.*`、碰撞/导航数据。
- 不要重新烘焙街区；不要动 `derived/` 里已有派生件。

## 交付记录

（Codex 在此追加）
