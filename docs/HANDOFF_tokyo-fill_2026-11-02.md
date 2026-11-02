# 交接：谷中 80×80 片区 + 浅草寺拼接（给接手的 Claude / Codex）

写于 2026-11-02 晚，5070 本机 Claude（额度将尽）。先读本文，再读 `projects/tokyo-fill/README.md` 和 `projects/tokyo-fill/REVIEW_ROUNDS.md`。

## 1. 已定的事（用户在本会话里确认）

- 主地点：**谷中**（接 qs_h1 台阶样板 + 5070 Ti 的 A、B 街块）。谷中部分**尽量按真实地形和真实地块**做（PLATEAU、OSM、国土地理院 DEM）。
- 浅草寺：雷门、宝蔵门、五重塔以**虚构拼接**放进谷中，不按两地真实位置；不能占用已按真实资料建模的谷中地块。
- 质量：每次改动至少 5 轮“渲染 → 看图 → 写最差三个问题 → 改”，重点是墙面纹理、地面质感、空调等设备细节。
- **仓库里可能已有队友完成的内容，重复的不要做。**

## 2. 现在的成果

分支 `tokyo-5070-fill`（未合并到 main，合并前要问用户）。目录 `projects/tokyo-fill/`：

| 街块 | 内容 | 状态 |
|---|---|---|
| C | 东北：五层 RC、工艺作坊、窄楼、N27 小巷和巷北一排 | GLB 已导出 |
| D | 东南：两栋真实公寓后楼（OSM，PLATEAU 缺）、斜路、投币停车场、岔口小广场 | 同上 |
| E | 主街西延到 E −124（谷中银座店面）、背街一排（含本授寺本堂、木造公寓）、E≈−58 真实十字路口（拆了 qs_h1 的 `h_G-14`、`h_G15`）、西段电杆电线 | 同上 |
| S | 浅草寺拼接：雷门（大提灯「雷門／風雷神門」）、宝蔵门（「小舟町」）、五重塔、参道、石灯笼、常香炉，位于 D 停车场以南的真实墓地用地 | 同上 |
| X | 远景：周边约 250 米 994 栋 PLATEAU 体块 + 谷中墓地 | 同上 |

总装：`src/assemble.py` 打开 `D:\Cijian\blend\qs_h1.blend`（只读），删掉路口两栋楼和 `far_*` 远景卡片，导入 A、B、C、D、E、S、X 七个 GLB，补上 qs_h1 缺的天空和太阳（`set_light`，参数照搬 `qs_build.py`）。**qs_h1.blend 直接打开渲染是全黑，这是原因。**

一轮检查：`powershell -File src\qa_round.ps1 -Tag qN`（重建全部街块 → 总装 → 15 个机位 → `output\assembly\sheet_qN.jpg`），5070 上约 15–20 分钟。

## 3. 本机文件位置（5070，`D:\project\cijian\work`）

- `src/`：全部脚本（和仓库 `projects/tokyo-fill/src` 相同）。根路径写死在 `blk_core.py` 的 `ROOT`。
- `data/`：PLATEAU（`plateau_near.json`）、DEM、OSM、航拍，均可用 `fetch_*.py` 重新下载。
- `assets/tex2k(_lite)/`：Poly Haven CC0 贴图；`assets/gen/`：生成的招牌、提灯、井盖、路面字、立面贴图；`assets/fonts/`：OFL 字体（不入库）。
- `blend/tokyo80_assembly.blend`：最新总装（225 MB+，不入库）。
- Blender：`D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe`；Python 依赖装在 `work\.pydeps`（运行前设 `PYTHONPATH`）。

## 4. 未完成 / 下一步（按优先级）

1. **先核对队友成果，避免重复**（本会话结束时刚 fetch 到）：
   - `origin/tokyo-5060-props`（Ksharklab，20:24）：店面、街道道具、路面砖、QA 渲染。**和我做的程序化店面装修（`blk_fill.py` 的 `shopfront/_fit/goods`）、设备（`blk_equip.py`）有重叠。** 应优先用 5060 的道具：按各街块 meta 里的 `anchors`（`storefront`、`ac_outdoor`、`bicycle` 等，坐标已是 qs_h1 世界系）摆放，再决定关掉我的哪部分（`Block.equip = 0` 可关设备；店面装修目前没有开关，需要加）。
   - `origin/codex/library-character-5060`：图书馆和人物模型，和建模区不重叠。
   - 提交 `321208d docs: add photo mode research handoff`（luzh06，20:34）先看一下内容。
2. **确认推送完成**：本会话最后一次 `git push`（提交 `a6d491e`，约 300 MB LFS）在后台运行，未确认结束。用 `git ls-remote --heads origin tokyo-5070-fill` 核对是否是 `a6d491e`；不是就在 `D:\project\cijian\nailong` 里重新 `git push`。
3. 光照贴图 UV + 烘焙（新街块只有 UV0；`shoplit` 和提灯纸是自发光材质）。
4. 进 Three.js 网页，游戏本有窗口实测帧率。新增约 230 万三角面（C 46 万、D 22 万、E 78 万、S 78 万、X 8 万），GLB 共约 300 MB，需要抽共用贴图、做 LOD。
5. 已知画面问题（详见 `REVIEW_ROUNDS.md` 末尾）：神像只是轮廓级；X 体块近看简单；qs_h1 沿街楼背面是白墙；路口南腿口有 qs_h1 的电杆 `pole_Z`（挪了会断线）；A 街块自己的地面在岔口有浅色台阶边。

## 5. 规矩（来自原交接文档和本会话）

- 不改 qs_h1、A、B 的源文件；只通过总装脚本删改。
- 每台机器在自己的分支提交，合并 main 前问用户；仓库公开，不提交凭据。
- 招牌一律虚构店名；浅草寺提灯写真实地标字，但不放捐赠企业名。
- 新素材登记到 `projects/tokyo-fill/asset-register.csv`（PLATEAU、OSM、国土地理院需署名）。
- 建楼前 `check_overlaps()` 会检查和其他楼、qs_h1、A、B 是否重叠，有重叠就退出码 3，不要用 `ALLOW_OVERLAP` 绕过。
