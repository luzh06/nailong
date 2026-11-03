# Claude Code / DeepSeek 分工提示词

你与 Codex 正在同一台 Windows 电脑、同一份代码里协作。本轮只完善东京主场景的移动和操作体验。相机、开场、NPC、剧情、转场、人物设置由其他人开发，请勿重做。

## 工作位置和所有权

仓库：`D:\project\chatgpt\ci\nailong`
项目：`projects/tokyo-world/`
可运行副本：`D:\project\chatgpt\ci\output\tokyo-three`
现有页面：`http://127.0.0.1:8780/web/index.html`

Codex 独占：world.js、index.html、collision.mjs、navigation.json、collision.bin、地图组件和地图资产、场景清单、模型/纹理/烘焙、资源压缩、服务和打包脚本、最终总装。

你只创建/修改以下文件：
- `projects/tokyo-world/web/experience-controls.mjs`
- `projects/tokyo-world/web/experience-controls.css`
- `projects/tokyo-world/tests/experience-controls.test.cjs`
- `projects/tokyo-world/tests/experience-controls-harness.html`
- `projects/tokyo-world/CONTROLS_HANDOFF.md`

你不是独自在代码库。不要覆盖别人的编辑，不要切分支/合并/推送，不要修改上述所有权之外的文件。现有 world.js 可只读。最终由 Codex 接线和复制到可运行副本；你不改运行中的网页入口。

## 先研究实际案例

阅读并记录具体可采用做法：
1. Three.js r170 官方 FPS：https://github.com/mrdoob/three.js/blob/r170/examples/games_fps.html
2. NippleJS 触屏摇杆：https://github.com/yoannmoinet/nipplejs
3. Sketchbook 输入/角色状态分离：https://github.com/swift502/Sketchbook （已归档，只参考架构）
4. Rapier 角色控制：https://rapier.rs/docs/user_guides/javascript/character_controller/ （只理解移动意图与碰撞修正的分离，物理实现由 Codex 负责）

使用原生 ES module、Pointer Events 和现有工具即可。使用开源代码前核对许可，注明借用范围；不要引入框架或替换当前 Three.js r170。

## 固定接口

导出 `createExperienceControls(options)`：

```js
const controls = createExperienceControls({
  canvas,                 // Three.js renderer canvas
  container: document.body,
  onLook: ({dx, dy, source}) => {}, // 原始像素增量，右移 dx>0，下移 dy>0
  onZoom: ({deltaY, source}) => {}, // 只发出缩放意图
  onExit: ({reason}) => {},        // escape / pointerlock-lost 等
  onHint: (text) => {}             // 简短、准确的操作提示
});
controls.setMode('view'); // 'view' | 'walk' | 'blocked'
controls.getMoveIntent(); // {forward: -1..1, right: -1..1, sprint: boolean}
controls.reset();
controls.dispose();
```

`getMoveIntent` 只返回输入意图，不修改相机/玩家位置，不做碰撞，不读取导航文件。Codex 每帧读取它，再通过统一碰撞控制器移动。

## 需要完成的体验

1. 键鼠：WASD/方向键移动；左右 Shift 都可加速；对角线归一化，不能更快。
2. 视角模式：按住画布拖动环视，滚轮发出缩放意图。点菜单、地图和其他按钮不应旋转画面。
3. 行走模式：进入时尝试 Pointer Lock；拒绝/不可用时平滑降级为拖动环视，仍能 WASD 移动。不要产生 unhandled rejection。
4. 手机/平板：左下独立触屏摇杆控制移动，右侧画布拖动看向；两个 pointerId 分开管理，能够同时操作。手指松开、pointercancel、切后台都立即停止。
5. Esc 退出；失去鼠标锁、窗口失焦、visibilitychange、切换模式时清空按键和摇杆状态，避免自动走动。退出提示恢复为视角模式提示。
6. UI 打开时宿主调用 setMode('blocked')：清空移动、释放锁定、禁用画布环视；关闭后由宿主恢复模式。
7. 焦点在输入框、textarea、select、contenteditable 时不拦截键盘。行走按钮保持焦点时仍可处理 WASD，避免已有 bug。
8. 模式切换不重复注册监听器。dispose 后移除监听器、触屏控件和 pointer capture；重复创建/销毁不泄漏。
9. 只把触屏摇杆、操作帮助和必要的退出控件放进自己的容器。苔绿/暖纸/少量朱红，与现有场景地图协调。地图预留右下，摇杆放左下，手机按钮至少 44px，支持焦点可见和 reduced-motion。

## 测试和交付

用独立 harness 测试，不改主入口。至少验证：WASD、左右 Shift、对角线、按住后失焦、Pointer Lock 拒绝、Esc、触屏双指移动+看向、pointercancel、blocked 模式和重复销毁。

CONTROLS_HANDOFF.md 写清：改动文件、导出接口、已执行的测试与证据、仍有的问题、Codex 在 world.js 中应替换的旧监听器位置。不要只声称“应该可用”。

完成后停止，不扩展到世界坐标、碰撞、模型、地图、相机模块或叙事模块。
