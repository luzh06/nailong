# 悉尼港白模（Blockout）

站在北岸 Kirribilli / Milsons Point 远眺歌剧院、CBD 与海港大桥的网页漫游白模。只用于确认构图、比例与可行走范围，不是最终美术。

## 运行

```powershell
D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe -m http.server 8770 --bind 127.0.0.1 --directory web
```

打开 <http://127.0.0.1:8770/>。拖动鼠标环视，WASD 行走，Shift 快走；“自由飞行”下 Q/E 升降，用来检查全场。

## 重建

```powershell
$blender = 'D:\Cijian\tools\blender-5.2.3-windows-x64'
& "$blender\5.2\python\bin\python.exe" -m pip install --target .pydeps shapely pillow   # 只需一次
& "$blender\5.2\python\bin\python.exe" scripts\prep_osm.py                       # data/*.json -> data/scene.json
& "$blender\blender.exe" -b --factory-startup -P scripts\build_blockout.py       # -> blend/ + web/data/
```

`data/osm_*.json` 是 2026-11-02 从 Overpass 拉取的 OSM 原始数据；需要更新时重新下载即可。

`data/nsw_dem_4m.tif` 是 NSW Spatial Services 5 m 高程（`maps.six.nsw.gov.au` 公开 ImageServer `NSW_5M_Elevation`，裸地，航测立体像对生成）按 4 m 导出的 GeoTIFF，下载命令写在 `scripts/terrain.py` 开头。抽样核对：歌剧院地面 3.4 m、Circular Quay 2.1 m、Martin Place 19.1 m、Observatory Hill 42.9 m。不要换成 AWS Terrain Tiles：那是含建筑的表面模型，CBD 地面会被抬高 40 m 以上。

## 体积与压缩

`blockout.glb` 约 2.1 MB（未压缩时 27 MB），没有降低网格或删减内容，做法是：

1. 地形网格顶点已焊接，改为平滑着色后导出器可以共用顶点（27 → 15 MB）；海堤四边形各自独立顶点，仍是硬边。
2. Draco 压缩，量化精度远高于默认：位置 20 bit（4.5 km 地面网格误差约 2 mm，远小于行走带 8 cm 抬高）、法线 14 bit（15 → 2.1 MB）。网页通过 `vendor/three/examples/jsm/libs/draco/` 里的解码器加载（Apache-2.0）。

验证方法：`?still=1` 冻结水面动画，同机位截图逐像素比较（同一场景两次渲染差值为 0）。四个机位（出生点、全景、歌剧院正面、脚下地面）中，Draco 带来的差异是 ≤0.53% 的孤立单像素，几乎都在水面倒影的高频扰动里，放大并排肉眼无法区分；平滑着色只改变地形坡面明暗，消除了刻面感。

## 内容与坐标

- 单位米，原点为悉尼歌剧院。Blender 中 x 东 / y 北 / z 上；网页中 x 东 / y 上 / -z 北。
- `L0_Ground`：OSM 海港水域反算的陆地，按 10 m 网格贴合 NSW 高程（岸边最低 1.5 m，沿岸立海堤到水下）；公园按网格上色；可行走带（沿岸约 3.2 万 m²，挖掉桥墩和建筑）用 2.5 m 网格单独贴地，高出地面 8 cm。
- `L1_Bridge`：桥塔位置取自 OSM，尺寸按下表参数化。`BridgeLayout` 统一管理桥的局部坐标、桥面纵断面、拱弦线和桥墩位置；桥塔底座、桥墩和桥台的占地会从行走区挖掉。每侧 5 跨引桥，桥面下两条桁架梁，4 排成对花岗岩桥墩落在 NSW 地形上，桥端用整块桥台接地（南端地面 17.9 m、北端 27.9 m）。

  | 参数 | 取值 | 依据 |
  |---|---|---|
  | 拱跨 / 拱顶 / 桥塔 / 全长 | 503 m / 134 m / 89 m / 1149 m | Wikipedia；Pylon Lookout "Bridge facts"（2003） |
  | 拱桁架 | 28 个节间，弦杆中心距跨中 18 m、两端 57 m | Wikipedia |
  | 跨中净空 / 桥面宽 | 49 m / 48.8 m | Wikipedia；Pylon Lookout（另有网站转载为 53 m，以原始页面 49 m 为准） |
  | 桥台塔底座 | 沿桥 48 m × 横向 68 m，实心到桥面底 | Pylon Lookout |
  | 引桥跨数 | 每侧 5 跨 | IStructE；Railway Wonders of the World |
  | 纵坡 | 两侧 1:40 升至桥上最高点 | railtram.com.au |
  | 桥面结构厚 | 4 m（推算） | 1930 年代资料"桥面下净空 170 ft（51.8 m）"减 49 m 净空，加铺装；同时使跨中吊杆约 59 m，对上公布的最长吊杆 58.8 m |
  | 支座销高度 | 水面上 4 m（推算） | 销位于桥台塔底部、贴近水面（该处地面 2–4 m）；由此上弦端点约 62.5 m，约在桥塔三分之二高处，与照片一致 |
  | 跨中竖曲线 | 200 m 抛物线（推算） | 连接两侧 1:40 坡，跨中降 1.25 m |

  结果核对：跨中桥面 53.0 m、净空 49.0 m；吊杆长 6.1–59.2 m（公布 7.3–58.8 m）；桥面在桥塔处 47.2 m、桥端 39.9 m。北侧 1:38 的短坡段未单独建模（与 1:40 相差 0.1%）。
- `L1_OperaHouse`：OSM 外轮廓做 17 m 基座（无公开数值，按两张参考照片中基座约占 67 m 总高的 0.26–0.29 推算）；球面半径 75.2 m、最高点 67 m、平面 183 × 120 m 已对照 Wikipedia 核实；壳体按“所有壳取自同一球面（R≈75 m）”生成，两半沿同一方向投影到各自球面，脊线无缝。参数表 `OPERA_HALLS` 已按三处来源校准（2026-11-02）：
  - 平面：OSM 两块玻璃墙部件（way 690624100 / 690624152）定出两厅轴线和开口位置；
  - 侧面：大桥东南桥塔拍的照片（rheins，CC BY 3.0）定出壳体顺序、后退量和高度比，最高点 67 m；
  - 正面：Kirribilli 拍的照片（Kgbo，CC BY-SA 4.0）定出开口宽度、两厅间距、歌剧厅/剧院高度比约 1 : 0.82 和深色内退玻璃。
  - 复现参考机位对比：`?cam=-479,92,-233&look=-40,10,55&fov=21&time=day&hud=0`（侧面）、`?cam=40,22,-715&look=-1,30,34&fov=16&time=day&hud=0`（正面）。加 `&still=1` 可冻结水面做逐像素比较。
- `L2_Buildings`：OSM 约 7,900 栋楼，按 `height` / `building:levels` 挤出，立在轮廓最低角的地面上并下沉 1 m；100 m 以上用玻璃色。约 3,200 栋没有高度和层数，按类型给默认值（`prep_osm.py` 的 `TYPE_HEIGHTS`）：车库/棚屋 3 m，独立住宅 7 m，联排 8 m，`residential` 10 m，公寓 14 m，`building=roof`（无墙雨棚）做成离地 3.5–4.5 m 的薄板，其余 9 m。
- `web/data/scene_meta.json`：行走多边形（含洞）、行走带 2 m 高度网格（`ground`）、两个机位、地标锚点。网页行走时视点跟随地面高度，坡度超过 35° 的一步会被挡住（沿边滑动）。

## 已知差距

- 地形：远处 10 m 网格较粗。
- 大桥：桥端以外的道路（北侧是弯道，Wikipedia 称 "curved northern approach"）不在远眺范围内，没有建模，桥台在桥端直接落地。拱弦线用抛物线近似。
- 高程许可证：服务元数据只写 "DFSI 2019"，Data.NSW 上该数据集标注 "License Not Specified"；NSW 政府网站默认 CC BY 4.0，Spatial Services 的框架文件写的是 CC BY 3.0 AU。当前按 "© State of New South Wales (Spatial Services)" 署名；公开发布前建议向 Spatial Services 书面确认。数据精度：水平 ±1.25 m、垂直 ±0.9 m（95% 置信）。
- 歌剧院：轮廓和比例已校准，但壳体无厚度、无肋线和瓷砖纹理，基座是整块挤出（无台阶、无大台阶）；前排壳在正面看仍比照片略窄。大桥桁架和引桥桁架为示意，无铁路/车道细节。
- 水面法线是程序生成的，近处偏平；没有船、灯光、夜景。
- 无高度标注的楼按类型估高，个别 `building=yes` 的 CBD 楼仍可能偏矮。

数据：© OpenStreetMap contributors（ODbL）；高程 © State of New South Wales (Spatial Services)。两者均已在网页右下角署名。three.js r170（MIT）位于 `web/vendor/three/`。
