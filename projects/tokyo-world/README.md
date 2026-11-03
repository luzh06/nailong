# 此间 · 东京主场景

完整运行包：`D:\project\chatgpt\ci\output\tokyo-three`。
双击其中的 `打开此间.cmd`，访问 <http://127.0.0.1:8780/web/index.html>。
使用开启硬件加速的 Edge / Chrome；依赖均为本地 Three.js r170，无需 CDN。
部署时保留整个运行包的 `web/`、`assets/`、`bake/`、`licenses/`，只上传 web 不完整。

## 游戏版（默认入口）

打开即为《此间 · 三日归途》可玩版本：开场古书 → 借阅卡选人 → 东京第三人称游览、三个图鉴点、NPC 相遇与互拍、入夜烟花 → 书页门 → 悉尼书页终章与四人回忆卡。
详见 `GAME_LAYER_2026-11-03.md`。原展示模式：`index.html?classic`（下面「操作」一节适用于展示模式）。

## 操作

- 七个机位；鼠标拖动环视、滚轮调视角。
- 进入行走后 WASD / 方向键移动，左右 Shift 快走，Esc 退出。
- 手机左侧摇杆移动，右侧拖动环视，可双指同时操作。
- M 展开地图，Esc 收起；地图或来源面板打开时停止移动。
- 流畅 / 标准 / 精细会调整分辨率、MSAA、阴影及泛光。
- 保存照片下载当前实际画面的 PNG，不带 HUD。

## 场景与边界

原台阶烘焙段 + A/B/C/D/E 街区 + S 寺院 + X 远景；34 个原有道具摆位。
新增 J 修复路口完整楼体、山墙、地坪和路缘；六轮记录见 MODEL_REFINEMENT_2026-11-03.md。
新增 L 是独立派生石铺通路，连接 D/S 缝隙、雷门和宝蔵门基座，不覆盖原始工程。
正式核心区为 80×80 米，台阶、商店街西延和寺院属于扩展区。
谷中与浅草寺是明确的虚构拼接，不能据此理解真实东京地理。

地图按当前交付几何的三角面正投影生成；`web/map/map-provenance.json` 记录输入 SHA。
行走使用 0.25 米地面采样 + 451,406 个真实碰撞三角面，包含原道具 `_COL`。
玩家半径 0.28 米、身高约 1.66 米、最大踏步 0.32 米；移动按不超过 0.07 米子步检测。
空间网格仅负责查找附近三角面，窄相检测保留 Three.js 官方 Capsule 算法。
这是贴地角色控制器，尚不包含跳跃、自由落体或动态刚体。

台阶段沿用日落烘焙，其他街区为实时光照；全场没有重新统一烘焙。
外围仍有简化远景和旧烘焙接缝，不能称为所有角落均已照片级精修。
开场、第三人称人物与相机、NPC、剧情、转场与拍照已由游戏层 `web/game/` 接入，见 `GAME_LAYER_2026-11-03.md`。
DeepSeek 独占输入模块及其测试，Codex 负责主入口接线；详见 `DEEPSEEK_TASK.md` 和 `CONTROLS_HANDOFF.md`。

## 验证

在仓库根目录：

```powershell
node --check projects/tokyo-world/web/world.js
node --test projects/tokyo-world/tests/collision.test.mjs projects/tokyo-world/tests/real-scene.test.mjs
node projects/tokyo-world/scripts/verify_routes.mjs
node projects/tokyo-world/tests/experience-controls.test.cjs
$py = 'D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe'
& $py projects/tokyo-world/tests/test_geometry.py
& $py projects/tokyo-world/tests/test_server.py
```

浏览器证据在 `output/tokyo-verification/`。实机路线报告 `runtime/report.json`；
三档与双指模拟 `round4-touch/report.json`；路线与来源以 `FINAL_STATUS_2026-11-03.md` 为准。
触屏模拟不是物理手机实测；单点帧率不能替代全地图性能结论。

## 重建顺序

当前优化后的运行包是权威资源。`prepare.py` 会从原始来源恢复更大的资产，
已有优化包默认拒绝覆盖；重做时选择新目录，不要对当前运行包重复 prepare。

1. `temple_access.py` 在独立 `derived/` 中生成通路 blend/GLB。
2. `prepare.py --out <新目录>` 整理基础资源、源码与派生模型。
3. `resize_baked.py` 做基础缩图，`optimize_delivery.py --exr --models` 做 HALF/几何量化。
4. 用实际最终包重建导航与碰撞（不再从旧 ig_v2.blend 直接提取）。
5. 用 `map_reference.py` 重建真实地图，复制源码数据到运行包。
6. 最后执行 `optimize_delivery.py --gzip --manifest`，避免过期 sidecar/字节数。

当前包的数据重建示例：

```powershell
$bl = 'D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe'
& $bl -b --factory-startup --python-exit-code 1 -P projects/tokyo-world/scripts/navigation.py -- --package 'D:\project\chatgpt\ci\output\tokyo-three' --out projects/tokyo-world/web
```

`serve.py` 仅监听回环地址，按 Accept-Encoding 提供新鲜 gzip sidecar，并保留 304 缓存。
HTTP 压缩改变传输体积，不改变解压后纹理/模型的 GPU 开销。来源及许可见运行包 `licenses/`。
