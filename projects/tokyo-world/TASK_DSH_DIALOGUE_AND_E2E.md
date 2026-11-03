# 给 DeepSeek（DSH）的任务：对白润色 + 游戏流程自动化回归测试（2026-11-03）

> 发起：Claude（本轮总装负责人）。分工按能力：Codex 做建模/骨骼（见 `TASK_CODEX_CHARACTERS.md`），你做**文字内容**和**测试**——你上一轮的 `experience-controls` 测试 harness（CDP、无 npm 依赖）做得很扎实，这次沿用同样做法。
> 两项任务互不依赖，可先做任务 2。完成后在本文件末尾追加「交付记录」。

## 你可以改的文件（只这些）

| 文件 | 权限 |
|---|---|
| `web/game/story-data.mjs` | **只改字符串内容**（台词、提示、卡片文案）；不改字段名、键名、坐标、函数结构 |
| `tests/game-flow.test.cjs`（新建） | 自由 |
| `tests/game-flow-notes.md`（新建，可选） | 自由 |

不要改 `world.js`、`web/game/` 下其他文件、`experience-controls.*`、模型、碰撞数据。发现游戏代码 bug：写进交付记录，由 Claude 修。

## 任务 1：对白润色（`story-data.mjs`）

依据：桌面《东京悉尼_MVP主线与接入方案 v0.2》（单玩家 + 三 NPC；东京只遇见情侣对象；另两人悉尼海滩才首次认识）。

- `PAIR_EVENTS`：四个玩家视角（rin / linchuan / camille / noah）。每个有 intro、hub 三组选项（只有 `key:true` 那组推进，另两组停留）、exchangeHint、gift、farewell。
- 要求：每句 ≤ 40 字；口语自然，避免翻译腔；人物性格（凛：主动迈出一步；林川：守时、习惯看地图；Camille：总在画外；Noah：拍别人的人）。
- 不得让玩家在东京见到另一对；不得出现真实店名/品牌；不要把“建议”写成既成事实。
- `finaleScript()` 中台词可润色，但 `reunion` 的两组核心对白方向（“今天不用看地图了？”/“这次，我先看见你了。”；“这次还替我拍吗？”/“这次，我们一起在照片里。”）已由用户确认，保留原意。
- 改完运行 `node --check web/game/story-data.mjs`。

## 任务 2：游戏流程 E2E 回归测试（`tests/game-flow.test.cjs`）

仿照 `tests/experience-controls.test.cjs`：Node 22+、`node:test`、CDP 启动本机 Chrome/Edge（**有窗口**，加 `--use-angle=d3d11` 或默认；无头会掉帧导致超时），不加 npm 依赖。

被测页：运行包服务 `http://127.0.0.1:8781/web/index.html`（`cd D:\project\chatgpt\ci\output\tokyo-three; python serve.py --port 8781`）。
调试参数：`?role=rin|linchuan|camille|noah&skipintro` 跳过开场（直接进东京）。就绪后页面有 `window.__cijian`（世界）和 `window.__cijianGame`（游戏层：`photo`、`journal`、`pair`、`phase`、`rig`、`avatar`、`partner`、`talk()`、`nightfall()`、`toFinale()`、`refresh()`）。
入城后要点一下 `.cj-curtain`（“点击画面，开始旅行”）才开始行走。

至少覆盖（每个角色各跑一遍 1–6）：
1. 加载：60 s 内 `__cijianGame` 存在；控制台 0 error、0 unhandledrejection。
2. 行走：派发 `keydown KeyW` 2 s 后 `__cijian.player` 位置变化，且 `walkWorld.ground` 不为 null。
3. TOKYO-01：把 `__cijian.me` 放到 `{x:1.2,y:12.5}`、`yaw=-π/2`，`photo.toggle()` → `photo.shoot()`，断言 `journal.has('TOKYO-01')`、出现 `.cj-reveal.on`。
4. 配对事件：传送到对方附近（凛/林川：`PLACES.sakuraNpc`；Camille/Noah：先 `nightfall()`，再到 `PLACES.fireworksNpc`），按 F → 空格推进 → 点第 3 个选项 → 断言 `pair.agreed`；再朝对方拍照 → 断言 `pair.exchanged` 且相册多出 2 张（玩家拍的 + 对方赠送的）。
5. 夜晚：`phase==='night'` 时 `__cijian.toneU.uGrade.value.x < 1`。
6. 终章：`toFinale()` 后 30 s 内出现 `.cj-endbar.on`，点“保存回忆卡”触发下载（可用 CDP `Browser.setDownloadBehavior` 落盘，断言 PNG 文件头）。
7. 截图：每个角色在 3、4、5、6 步各存一张到 `output/tokyo-verification/game-flow/<role>-<step>.png`，并**自己打开看一眼**，把最差的三个画面问题写进交付记录。

输出格式参照 controls 测试：`[game-flow] N/M passed`，失败项打印真实错误。

## 交付记录

（DSH 在此追加）
