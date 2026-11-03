# 输入与操作层交接（experience-controls）

> 2026-11-03 · 负责人：Claude Code / DeepSeek
> 范围：只做键鼠/触屏输入与操作体验；不碰相机、导航、碰撞、模型、地图资产或最终总装。
> 状态：模块、样式、独立测试和 harness 已完成；**等 Codex 在 `world.js` 中接线验收**。

## 1. 交付文件（只新增这些）

| 文件 | 说明 |
|---|---|
| `web/experience-controls.mjs` | 输入模块；只输出意图，不修改玩家位置/相机 |
| `web/experience-controls.css` | 触屏摇杆、操作帮助、退出控件；苔绿/暖纸/朱红 |
| `tests/experience-controls.test.cjs` | Node 测试：静态检查 + CDP 启动本机 Chrome/Edge 跑 harness |
| `tests/experience-controls-harness.html` | 独立测试页；不加载 Three.js、不改主入口 |
| `CONTROLS_HANDOFF.md` | 本文件 |

**未修改** `web/world.js`、`web/index.html`、`collision.mjs`、`navigation.json`、地图组件、模型/纹理/烘焙/服务脚本。`world.js` 只读参考。

## 2. 固定接口

```js
import { createExperienceControls } from './experience-controls.mjs';

const controls = createExperienceControls({
  canvas,                         // Three.js renderer canvas（必填）
  container: document.body,       // 控件容器（默认 document.body）
  onLook: ({ dx, dy, source }) => {},
  onZoom: ({ deltaY, source }) => {},
  onExit: ({ reason }) => {},
  onHint: (text) => {}
});

controls.setMode('view');         // 'view' | 'walk' | 'blocked'
controls.getMoveIntent();         // { forward: -1..1, right: -1..1, sprint: boolean }
controls.reset();
controls.dispose();
```

### 语义约定

- `getMoveIntent()`：`forward` = W/↑ 为正，S/↓ 为负；`right` = D/→ 为正，A/← 为负；对角线已归一化（模长 ≤ 1）；`sprint` = 左 Shift **或** 右 Shift。
- 模块**只返回意图**：不读导航、不读 collision、不写 `camera.position` / `me.x/y`。每帧由宿主读取后交给现有碰撞控制器。
- `onLook`：原始像素增量，**右移 dx>0，下移 dy>0**；`source` 为 `'lock'`（Pointer Lock 鼠标）或 `'drag'`（画布拖动，鼠标/触屏共用）。灵敏度与 pitch 夹紧由宿主决定。
- `onZoom`：`deltaY` 原样来自 wheel（`source:'wheel'`）。Ctrl/Meta+wheel 不拦截，留给浏览器缩放。
- `onExit`：`reason` 为 `'escape'`、`'pointerlock-lost'`、`'control-exit'`（触屏退出按钮）。宿主应把 `walking` 设为 `false` 并更新按钮；模块内部已回到 `'view'`。
- `onHint`：始终由模块给出当前模式的**唯一提示文本**；`blocked` 时为空字符串，宿主应隐藏提示元素。不要再用旧的 `$('hint').textContent = ...` 写入。
- 四个宿主回调（onLook/onZoom/onExit/onHint）中的异常会在模块边界被捕获：每个实例只 `console.error` 一次，输入状态机继续运行，不会冒到 `world.js` 的全局 error/fatal。宿主仍应修掉回调内部的异常。
- 可选的扩展参数（不属于固定接口核心，默认值已足够）：
  - `touch: true|false`：强制/关闭触屏 UI（测试或混合设备用）。
  - `pointerLock: true|false|'auto'`：默认 `'auto'`；有精细指针（鼠标）时尝试 Pointer Lock，触屏主设备直接使用拖动环视 + 摇杆。传 `true` 可强制尝试（触屏上若成功，任何触摸都会主动释放并退回拖动）。
  - `pointerLockTimeout`（默认 1200ms）、`deadzone`（默认 0.12）。

### 模式矩阵

| 模式 | 桌面 | 触屏 |
|---|---|---|
| `view` | 画布拖动环视；滚轮缩放；不移动 | 画布拖动环视；摇杆/帮助/退出隐藏；`onHint` 给拖动提示 |
| `walk` | 尝试 Pointer Lock；成功=鼠标环视，失败=拖动环视；WASD/方向键；左右 Shift；Esc 退出 | 左下摇杆移动；右侧画布拖动环视；两个 pointerId 独立；右下地图保留；触屏退出按钮 |
| `blocked` | 清空按键/拖动/摇杆，释放锁，禁用画布环视和滚轮；提示为空 | 同左，并隐藏全部触屏 UI |

其他状态规则：

- 窗口 `blur`、`visibilitychange`（hidden）、焦点进入 input/textarea/select/contenteditable、切换模式、Esc、Pointer Lock 丢失：立即清空键盘、摇杆、拖动和 pointer capture。
- 按钮（包括现有「进入行走」按钮）保持焦点时 WASD 仍然有效；只对真实可编辑控件让出键盘。
- Pointer Lock 请求返回 Promise 或 undefined 都不会产生 unhandled rejection；`pointerlockerror` 同样降级为拖动环视。`dispose` 之后才 resolve 的锁会被主动释放。
- 模式切换不新增监听器；监听器只在构造时注册，`dispose` 成对移除。
- `reset()` 只清临时输入，**不改变模式、不释放锁**；需要完全暂停 UI 时用 `setMode('blocked')`，需要拆除用 `dispose()`。

## 3. Codex 在 `world.js` 中的接入位置

> 与 Codex 的 `HANDOFF_CODEX_2026-11-03.md` 对齐：其第 9 节确认本模块文件归 DeepSeek，P1 明确要求“接 DeepSeek 模块前读 CONTROLS_HANDOFF，删除父旧键鼠监听器”；其 5.3 确认 `WalkWorld` 尚未接主循环。本模块的 `getMoveIntent()` 正好位于 `WalkWorld.move(...)` 之前，Codex 只负责意图→速度→碰撞修正。
>
> 以下行号基于 2026-11-03 01:25 读取的 `web/world.js`（34,912 字节，Codex 已加入地图 UI）。若已偏移，按代码片段搜索，不要按行号硬改。

| 当前代码 | 处理 |
|---|---|
| `:250 let walking=false;` | 保留；宿主仍用 `walking` 决定是否每帧应用移动 |
| `:252 requestWalkLock()` | **删除**；由 `controls.setMode('walk')` 内部请求/降级 |
| `:304 const keys={}` | **删除** |
| `:305-306 keydown/keyup/blur` | **删除**；模块处理 WASD/方向键/Shift/Esc/焦点/blur |
| `:307-313 dragging/pointerup/pointermove/wheel/pointerlockchange/mousemove` | **删除**；模块处理拖动/滚轮/锁定/环视 |
| `:314-319 walk(dt)` 的 `keys` 读取部分 | 改为读取 `controls.getMoveIntent()`；保留相机/eye/bob 和 `WalkWorld`/碰撞移动 |
| `:358 $('hint').hidden=false` | 保留元素；提示内容交给 `onHint` |
| `:359-360 地图 UI 与 cijian:mapchange` | 保留 `createMapUI()`；展开时 `controls.setMode('blocked')`，关闭时 `controls.setMode(walking?'walk':'view')`。不要再手动清 `keys`/`exitPointerLock`/写旧提示 |
| `:361 view select` | 退出行走后 `controls.setMode('view')`；保留 `toCam(...)` |
| `:362-366 行走按钮` | 进入：设置 `me` 后 `walking=true; controls.setMode('walk')`；退出：`walking=false; controls.setMode('view')`；删除 `requestWalkLock()`。**:363 的全景俯瞰拦截保留** |
| `:367 来源/credits` | 打开时 `controls.setMode('blocked')`；关闭时恢复 `walking?'walk':'view'` |
| `:375 主循环` | 保留 `mapUI.update(...)`；把 `if(walking)walk(dt)` 改为用 intent 移动 |
| `:370 window.__cijian` | 可把 `controls` 一并暴露，方便验收；非必须 |

### 推荐的接线片段

```js
import { createExperienceControls } from './experience-controls.mjs';

const controls = createExperienceControls({
  canvas,
  container: document.body,
  onLook: ({ dx, dy, source }) => {
    if (walking) {
      const s = source === 'lock' ? 0.0021 : 0.003;
      me.yaw -= dx * s;
      me.pitch = THREE.MathUtils.clamp(me.pitch - dy * s, -1.3, 1.3);
    } else {
      const eu = new THREE.Euler().setFromQuaternion(camera.quaternion, 'YXZ');
      eu.y -= dx * 0.003;
      eu.x = THREE.MathUtils.clamp(eu.x - dy * 0.003, -1.4, 1.4);
      camera.quaternion.setFromEuler(eu);
    }
  },
  onZoom: ({ deltaY }) => {
    camera.fov = THREE.MathUtils.clamp(camera.fov + deltaY * 0.02, 20, 90);
    camera.updateProjectionMatrix();
  },
  onExit: ({ reason }) => {
    walking = false;
    $('walk').textContent = '进入行走';
    // 模块内部已经回到 view；这里只同步宿主状态。
    // reason: escape / pointerlock-lost / control-exit
  },
  onHint: (text) => {
    const hint = $('hint');
    hint.textContent = text;
    hint.hidden = !text;       // blocked 时模块给空串
  }
});
controls.setMode('view');
```

移动部分（把旧 `walk(dt)` 的输入换成 intent，**位置仍由 Codex 的碰撞控制器决定**）：

```js
function walk(dt) {
  const { forward, right, sprint } = controls.getMoveIntent();
  const sp = (sprint ? 3.4 : 1.8) * dt;
  const yawX = Math.cos(me.yaw);
  const yawY = Math.sin(me.yaw);
  const dx = (forward * yawX + right * yawY) * sp;
  const dy = (forward * yawY - right * yawX) * sp;
  // Codex 的 WalkWorld / capsule 碰撞在这里；模块不读导航、不改位置。
  // const next = walkWorld.move({ x: me.x, y: me.y, height: ... }, dx, dy);
  // me.x = next.x; me.y = next.y;
  // 然后保留原有 eye / bob / camera 更新。
}
```

- 进入行走：设置 `me`、`walking=true`、按钮文案后调用 `controls.setMode('walk')`；不要自己 `canvas.requestPointerLock()`。
- 退出行走：`walking=false`、按钮文案后调用 `controls.setMode('view')`；不要自己 `document.exitPointerLock()`。
- 地图展开/来源面板打开：`controls.setMode('blocked')`；关闭：按当前 `walking` 恢复 `'walk'` 或 `'view'`。地图自己的说明文字可以在 `setMode('blocked')` 之后写入 `#hint`；关闭后不要再写旧提示，交给 `onHint`。
- 触屏上会同时显示模块的帮助和退出按钮；如果宿主仍显示 `#hint`，建议在触屏行走时隐藏 `#hint`（或直接使用模块的 `onHint` 文本），避免同一提示出现两次。

## 4. 测试与证据

### 运行

```powershell
cd D:\project\chatgpt\ci\nailong\projects\tokyo-world
node tests/experience-controls.test.cjs
```

- Node 端：2 个 test（静态检查 + 浏览器 harness）。
- 浏览器端：本机 Chrome/Edge 无头（CDP，不依赖 npm 包）。
- 可用 `set XC_BROWSER=C:\path\to\chrome.exe` 指定浏览器。
- 手动打开：在 `projects/tokyo-world` 启动任意静态服务器，访问
  `http://127.0.0.1:<port>/tests/experience-controls-harness.html`。
  页面自动跑测试；点「创建触屏行走预览」可以在桌面强制显示触屏摇杆/帮助/退出。

### 本次实测结果（真实运行）

```text
[experience-controls] 18/18 tests passed in chrome.exe
  PASS  WASD / 方向键 / 对角线归一化 / 左右 Shift
  PASS  按住后窗口失焦：立即清零且可恢复
  PASS  visibilitychange 隐藏：立即清空按键和摇杆
  PASS  焦点在 input/textarea/select/contenteditable 时不拦截；按钮焦点仍可 WASD
  PASS  视角模式：画布拖动环视、滚轮缩放，UI 点击不旋转
  PASS  Pointer Lock 成功：锁定后鼠标环视、Esc 退出且提示恢复
  PASS  Pointer Lock 被浏览器夺走：onExit(pointerlock-lost) 且不残留移动
  PASS  Pointer Lock 拒绝：平滑降级、无未处理拒绝，WASD 仍可用
  PASS  pointerlockerror 事件：同样进入降级模式
  PASS  Pointer Lock API 不可用：直接降级，不抛异常
  PASS  触屏双指：左摇杆移动 + 右侧环视可同时操作，松手/取消即停
  PASS  触屏退出按钮：onExit(control-exit) 并回到视角模式
  PASS  blocked：清空移动/摇杆、释放锁定、禁用环视与滚轮
  PASS  dispose：监听器成对移除、DOM/样式清理、重复创建销毁
  PASS  dispose 时摇杆/环视仍在拖动也能清理
  PASS  dispose 后迟到的 Pointer Lock 也会被释放
  PASS  宿主回调抛错不打断输入，且只记录一次
  PASS  没有未处理的 Promise 拒绝
  browser: HeadlessChrome/156.0.0.0
```

交叉验证：

- 同一套测试在 **Microsoft Edge（msedge.exe，HeadlessChrome/156 + Edg/156）** 下再次运行：**18/18 通过**。
- 另用 Playwright MCP 的 Chromium（Chrome 156）打开同一 harness：**18/18 通过，console 0 error，0 unhandled rejection**。
- **独立 code-reviewer 复核**（针对 01:27 稳定快照）：APPROVE；0 CRITICAL / 0 HIGH / 0 MEDIUM；唯一 LOW 是 onLook/onZoom 未隔离宿主异常，已修复为四个回调统一 try/catch + 单次 `console.error`，并新增“宿主回调抛错”回归测试。复核结论见本文件第 4 节测试项。
- 计算样式/布局实测：
  - 390×844：摇杆 128×128，left 16，right 144；帮助宽 128、right 144；退出 44px 高、top 132；地图（190px，right 12）左边界 188 → 不重叠。
  - 360×640：摇杆 104、right 116；帮助宽 104、right 116；地图左边界 158 → 不重叠。
  - 640×360 横屏：帮助隐藏；摇杆 left 16–144；退出移到 x 160–219（不压摇杆），地图左边界 438。
  - `prefers-reduced-motion: reduce` 下摇杆/退出 transition 为 0s；`view` 时摇杆/帮助/退出均隐藏，`walk` 时恢复。
- 失败输出位置：harness 的 `#xc-results` JSON、页面标题和 `window.__XC_TEST_RESULTS__`；Node 测试会打印失败项和真实错误。

**测试边界**：无头浏览器无法真正提供 Pointer Lock，测试用可控的 `document.pointerLockElement` / `canvas.requestPointerLock` 桩；触屏用合成 PointerEvent。真实设备上仍需点一遍：Pointer Lock 授权/拒绝、双指同时摇杆+环视、切后台返回。测试不能替代这轮人工验收。

## 5. 参考实现与许可

只借鉴架构/交互，没有复制第三方源码，也没有新增 npm 依赖。

| 参考 | 具体借鉴 | 许可 |
|---|---|---|
| three.js r170 `examples/games_fps.html` | `keyStates` 按 `event.code` 记录；`mousemove` 只在 `pointerLockElement` 命中时消费；移动方向拆成 forward/side，物理/位置更新在输入之后单独进行 | MIT |
| three.js r170 `PointerLockControls.js` | `connect/disconnect` 成对增删 document 监听；`pointerlockchange`/`pointerlockerror` 分开处理；Euler YXZ 与 pitch 夹紧思路（本模块只发原始增量，夹紧交给宿主） | MIT |
| NippleJS | static 摇杆固定在左下；按 pointer identifier 归属；`vector` 单位方向 + `force` 力度 + 死区；`start/move/end` 与 `destroy` 清理；容器必须定位 | MIT |
| swift502/Sketchbook（已归档） | `InputManager` 集中收事件并转发给 `IInputReceiver`；动作表与 `resetControls`；移动向量相机相对、归一化；输入层不直接改角色位置 | MIT |
| Rapier character controller 文档 | `desiredTranslation` → `computeColliderMovement` → `computedMovement` 的分离；本模块只给“想怎么走”，碰撞修正/autostep/snap 由 Codex 的 `WalkWorld` 负责 | Apache-2.0（仅阅读文档） |

## 6. 已知问题/限制

1. **真实 Pointer Lock 与真实触屏**尚未在物理设备上验收；harness 是桩 + 合成事件。请 Codex 在接线后用 Edge/Chrome 实机点一次。
2. `pointerLock:'auto'` 在触屏主设备上不请求锁（直接拖动环视 + 摇杆）；这是为了避免移动端无意义的锁定。若要“所有设备都先试一次”，传 `pointerLock:true`。锁成功后任何触摸会主动释放锁并切回拖动。
3. 少数旧浏览器 `requestPointerLock()` 返回 `undefined`；`dispose` 恰好发生在“请求已发出、锁稍后才授予”的窗口时，可能留下一次晚到的锁。现代 Chrome/Edge 的 Promise 分支已处理并在测试中覆盖；旧浏览器请保持 `dispose` 与销毁页面同时发生。
4. 不实现双指捏合缩放、手柄、触摸惯性；滚轮缩放意图由宿主应用。触屏摇杆没有单独的冲刺手势（Shift 仅桌面）。
5. 模块只发 raw `dx/dy`，不决定灵敏度、pitch 夹紧、相机模式；宿主必须按现有 `me.yaw/me.pitch` 或 `camera.quaternion` 应用。
6. 地图/来源面板必须由宿主调用 `setMode('blocked')`；模块不知道面板是否打开。当前 `world.js` 的地图 handler 在展开时会把 `walking=false`，关闭时请按宿主状态恢复 `'view'`（或保留暂停状态、关闭后恢复 `'walk'`）。
7. 模块的 CSS 根节点 `z-index:4`，低于现有地图的 `z-index:5`、高于 canvas；如果 Codex 调整地图 z-index，需同步检查。摇杆/帮助在左下，地图在右下；360/390/640 布局已实测不重叠。
8. 触屏上模块会显示自己的帮助与退出按钮；若宿主仍显示 `#hint`，请隐藏或只保留一个，避免重复提示。`onHint('')`（blocked）时宿主应隐藏 `#hint`。
9. `dispose` 会恢复 canvas 的 inline `touch-action`；宿主不要在模块生命周期内同时设置 `canvas.style.touchAction`。
10. Node 测试用 `fetch`/`WebSocket`（Node 22+；本机 Node 24）和本机 Chrome/Edge；无 npm 依赖。若 CI 没有浏览器，设置 `XC_BROWSER` 或只在本地跑 harness。
11. 现有 `world.js` 中旧的 Pointer Lock / 拖动 / 滚轮 / key 监听仍存在，接线时必须按第 3 节删除，否则会与模块重复触发（尤其 mousemove 和 pointerlockchange）。

## 7. 交接结论

- 本模块可独立运行、测试通过；接口按任务书固定，未扩展到世界坐标/碰撞/模型/地图/相机/叙事。
- Codex 只需：复制 `web/experience-controls.mjs` + `web/experience-controls.css`，按第 3 节替换 `world.js` 旧监听与 `walk` 输入部分，给地图/来源面板补 `blocked` 模式，然后跑一次第 4 节测试和真实设备验收。
- 我在此停止，不继续改 `world.js` 或运行副本；由 Codex 统一接线与验收。
