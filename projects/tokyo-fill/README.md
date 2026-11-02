# 谷中 80×80 米片区补全（5070）

在 `yuyake-dandan` 的台阶样板（qs_h1）和 5070 Ti 的街块 A、B 之外，补齐 80×80 米可自由行走片区剩下的三块：C（东北）、D（东南）、E（西段和背街一排），并打通真实的十字路口。按用户 11-02 的要求，地点定为谷中，布局和地形尽量按真实资料做。

状态：Cycles 预览、GLB 导出、与 qs_h1 和 A、B 的总装渲染已完成。**未烘焙，未进 Three.js，未在游戏本浏览器里实测帧率。** 只有 UV0。

## 范围

80×80 米取 qs_h1 模型坐标 x −40…40、y −80…0，换成 ENU 约为 E −112.5…−32.5、N −38…42，原点是夕焼けだんだん台阶顶。台阶本身（y 0…16）在这个正方形东边，是原有样板。

| 部分 | 内容 | 来源 |
|---|---|---|
| qs_h1（原有） | 主街 64 米、台阶、沿街楼、电杆电线 | 5070 样板 |
| A、B（原有） | 主街南、北两侧的背街街块 | 5070 Ti |
| **E（本次）** | 主街向西延伸到 E −124；主街与 A 小巷之间的一排；十字路口南北两条腿 | PLATEAU、OSM |
| **C（本次）** | 东北：五层 RC、工艺品作坊、四层窄楼、N27 小巷和巷北一排 | PLATEAU |
| **D（本次）** | 东南：两栋真实公寓的后楼、斜路、投币停车场、岔口小广场 | OSM、航拍 |

覆盖图：`preview/cover_plan.png`（PLATEAU 轮廓、已有物体、A/B、目标正方形）；`preview/aerial_ref.jpg`（国土地理院航拍，仅作参考）。

## 按真实资料做了什么

- **楼的位置和尺寸**：全部取自 PLATEAU 台东区 2025（网格 53394671）的建筑轮廓、实测高度和层数，只在两种情况下裁切：贴着 qs_h1 沿街楼背面，或者会压到 A、B 的路。
- **PLATEAU 缺的楼**：东南角 PLATEAU 只有一根细条，航拍和 OSM 显示是两栋公寓：コージーコート谷中（6 层）和ウィルローズ谷中銀座（7 层）。按 OSM 轮廓做了它们露在 qs_h1 沿街楼后面的部分。
- **真实地物**：E 排的大屋是本授寺（OSM 记为佛寺），做成入母屋瓦顶本堂和一对石灯笼；主街北侧 E −98 有一道真实的铁门和步道（OSM），通向 B 的侧巷；岔口长椅位置取自 OSM。
- **主街是谷中银座商店街**：西段沿街楼底层都做成店面（玻璃拉门、敞开货架、格子门加暖帘），对应 OSM 里同位置真实存在的面包、熟食、杂货等店。**招牌全部是虚构店名。**
- **路**：用 PLATEAU 道路面判定路面；主街西段按真实路缘线，在 24 米内从 qs_h1 的直街平滑过渡到真实街线（真实街道在这里往北偏约 2.5 米）。
- **十字路口**：真实路网在 E≈−58 有一条南北路。拆掉了 qs_h1 挡在路口的两栋沿街楼 `h_G-14`、`h_G15` 及其雨棚，路口南腿接 A 的斜路，北腿接 B 的东路。
- **地形**：A、B 用的是 PLATEAU 地面高程的东西向拟合（±0.45 米），新街块沿用它，保证接缝对齐；E −54 以东再叠加国土地理院 5 米 DEM 的横向起伏（东南角向南升约 0.6 米）；贴近 qs_h1 主街的 7 米内平滑过渡到主街的 z=0。

和真实不一致、需要知道的地方：

- qs_h1 的主街是平的、直的，真实街道西低东高约 1.7 米并略弯。这是原样板的取舍，本次没动。
- qs_h1 的 `apt_G2` 占了本授寺前半，本堂只能做后半（进深约 5 米）。
- 公寓只做了露出的部分；qs_h1 在这里的沿街楼是两层小楼，和真实的 6、7 层不一致。
- 路口北腿正中有一根 qs_h1 原有的电杆，暂时保留，没挪。

## 交付内容

| 文件 | 用途 |
|---|---|
| `block_X/block_X.glb` | 模型，内嵌贴图和顶点色，已在 qs_h1 世界坐标，导入后不用移动 |
| `block_X/block_X_meta.json` | 建筑清单、三角面统计、店面和道具预留位（`anchors`，给 5060） |
| `block_X/preview/` | 单街块 Cycles 预览 |
| `assembly/` | 总装渲染（日落预设，与 qs_h1 原渲染同一套灯光参数）：`before_*` 是原 qs_h1，`after_*` 是 qs_h1+A+B+C+D+E，同机位同设置。`stairs_west` 就是 qs_h1 自己的 `cam_west` 主机位 |
| `asset-register.csv` | 本次新增素材和数据的来源、许可登记 |
| `src/` | 生成脚本，可完全重建 |
| `data/` | qs_h1 物体占地框、DEM 网格、招牌图集坐标 |
| `assets/` | 招牌图集 `signs.jpg`、暖帘图集 `noren.jpg`（本项目生成） |

| 街块 | 三角面 | GLB |
|---|---|---|
| C | 352,674 | 45.2 MB |
| D | 170,828 | 26.0 MB |
| E | 602,354 | 59.8 MB |

总装文件 `tokyo80_assembly.blend` 太大，不入库，在制作机 `D:\project\cijian\work\blend\`，可用 `src/assemble.py` 从 qs_h1 和五个 GLB 重新生成。

## 坐标

和 A、B 完全一致：ENU 米，原点为 OSM 夕焼けだんだん台阶顶（35.727641, 139.767341）；换到 qs_h1：`x = 1.8 − N`，`y = E + 32.5`，z 为模型高度（主街 z=0）。

## 总装时要做的事

1. 删除 qs_h1 里 `h_G-14`、`h_G15` 两栋楼，以及中心落在路口范围（ENU E −61.2…−52.6，N −8.7…12.3）内的 `aw_*` 雨棚。`src/assemble.py` 里的 `h1_removed()` 就是这条规则。
2. 把 qs_h1 的 `ground_far` 下移 0.4 米，否则西段新地面（最低 −0.46）会被它盖住。
3. 新街块只有 UV0，烘焙前要生成光照贴图 UV，和 A、B 一样。
4. 店面里的发光内景用的是 `shoplit` 材质（自发光），烘焙时按灯处理，或在网页里单独控制强度。
5. `qs_h1.blend` 存盘时没有天空和太阳（原来由 `qs_build.py` 渲染时临时加），直接打开渲染是全黑。`assemble.py` 的 `set_light()` 照搬了 `qs_build.py` 的 morning、sunset 两套参数。

## 已知问题（自己看图记下的）

- 东南角 A 街块自己的地面在岔口附近有几块浅色台阶状边缘（A 的地面格子比路面高 6 厘米），本次没改 A。
- qs_h1 的沿街楼背面和侧面大多是白墙、没有窗，拆开路口后从北腿和南腿能看到。
- 西段延长部分没有电杆和电线；qs_h1 的电线到 E≈−85 为止。
- 店面货架上的商品是彩色方块，近看会露馅，留给 5060 的店面道具替换（`anchors` 里有 `storefront` 预留位）。

## 重新生成

制作机路径是 `D:\project\cijian\work`，换机器改 `src/blk_core.py` 的 `ROOT`。所需数据都由脚本下载：

```powershell
$py = 'D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe'
$bl = 'D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe'
& $py -m pip install --target .pydeps lxml pillow shapely        # 只需一次，之后 $env:PYTHONPATH='.pydeps'
& $py src\fetch_plateau.py; & $py src\parse_plateau.py; & $py src\fetch_osm.py; & $py src\fetch_poi.py
& $py src\fetch_dem.py; & $py src\fetch_aerial.py; & $py src\fetch_tex.py
& $py src\arm1k.py; & $py src\tex_neutral.py; & $py src\arm1k.py; & $py src\tex_lite.py; & $py src\gen_atlas.py; & $py src\gen_signs.py
& $bl -b --factory-startup -P src\blk_e.py -- --export 1 --render 0   # C、D 同理
& $bl -b D:\Cijian\blend\qs_h1.blend -P src\assemble.py -- --save 1
```

`blk_fill.py` 是三块共用的工具：真实地形函数、已有物体避让、PLATEAU 道路判定、地面、店面装修、预览和导出。生成前会检查每栋楼是否和其他楼、qs_h1、A 和 B 重叠，有重叠就停下（退出码 3），不会悄悄生成穿模的模型。

## 来源和许可

| 内容 | 来源 | 许可 |
|---|---|---|
| 建筑轮廓、高度、层数、道路面 | 国土交通省 Project PLATEAU，台东区 2025，网格 53394671 | 需署名，对外发布前请核对官网现行条款（政府标准利用规约 2.0 / CC BY 4.0） |
| 公寓轮廓、店铺和寺院位置、铁门、长椅 | OpenStreetMap | ODbL，署名 © OpenStreetMap contributors |
| 5 米 DEM、航拍参考图 | 国土地理院 地理院タイル（dem5a、全国最新写真） | 需署名「国土地理院」；航拍只作参考，没有用作贴图 |
| PBR 贴图、天空 | Poly Haven | CC0 |
| 招牌字体 | Zen Old Mincho、Yuji Syuku、Zen Kaku Gothic New、Klee One（Google Fonts） | SIL OFL 1.1，只把文字烘进图集，字体文件不入库 |
| 招牌、暖帘图集，污渍图集 | 程序生成（`gen_signs.py`、`gen_atlas.py`） | 本项目自制，店名均为虚构 |
| 生成器核心 `blk_core.py`、`blk_arch.py` | 5070 Ti 的 `projects/tokyo-blocks/src`，只改了根路径 | 本项目 |
