# 悉尼港 · 网页漫游场景

站在北岸 Kirribilli / Milsons Point 远眺歌剧院、CBD 与海港大桥的网页漫游。几何来自真实数据（OSM、NSW 高程）并经过校准，材质、天空、光影、水面和夜景已做真实化处理；拍照模块尚未加入。

## 运行

```powershell
D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe -m http.server 8770 --bind 127.0.0.1 --directory web
```

打开 <http://127.0.0.1:8770/>。拖动鼠标环视，WASD 行走，Shift 快走；“自由飞行”下 Q/E 升降（后续直升机体验的基础）。左上角切换白天 / 黄金时段 / 蓝调（夜景灯光）。

URL 参数：`q=low` 低画质（2 级阴影、1024 阴影图、无 MSAA）；`time=day|golden|blue`；`cam=x,y,z&look=x,y,z&fov=` 指定机位；`hud=0` 隐藏界面；`still=1` 冻结水面；`trees=0` 不加载树；`bench=1` 暴露 `window.__bench(n)`（同步渲染 n 帧并回读像素，测真实帧耗时，不受后台窗口限帧影响）。

## 重建

```powershell
$blender = 'D:\Cijian\tools\blender-5.2.3-windows-x64'
& "$blender\5.2\python\bin\python.exe" -m pip install --target .pydeps shapely pillow   # 只需一次
& "$blender\5.2\python\bin\python.exe" scripts\prep_osm.py                       # data/*.json -> data/scene.json
& "$blender\5.2\python\bin\python.exe" scripts\fetch_assets.py                   # 纹理 / 天空 -> assets_src/ + web/assets/
& "$blender\5.2\python\bin\python.exe" scripts\build_landcover.py                # 地表遮罩 + 树 -> web/assets/ground/, web/data/trees.json
& "$blender\blender.exe" -b --factory-startup -P scripts\build_blockout.py       # -> blend/ + web/data/
```

脚本分工：`prep_osm.py`（OSM → 场景 JSON）、`terrain.py`（高程采样）、`meshkit.py`（网格与米制 UV）、`ground.py`（地形、海堤、步行区、建筑及其风格属性）、`bridge.py`、`opera.py`、`build_blockout.py`（组装、导出、元数据）、`build_landcover.py`、`fetch_assets.py`。`tools/review_shots.js` 是固定机位批量截图脚本（Playwright）。

## 真实化渲染（web/src/）

| 模块 | 内容 |
|---|---|
| `materials.js` | 按 glTF 材质名替换为真实材质；自定义着色器在 CSM 阴影补丁之后串接 |
| `shaders/facade.js` | 程序化立面：8 种风格（玻璃幕墙、办公、砂岩、砖、抹灰、住宅、附属、仓库）× 每栋随机种子；窗格抗锯齿、远处渐变为平均色；玻璃反射环境；屋顶混凝土 / 赤陶瓦 / 彩钢；夜间按楼层随机亮灯 |
| `shaders/ground.js` | 按地表遮罩混合铺装、沥青路、草坪、沙、砂岩，陡坡自动变岩石；双尺度采样消除重复；夜间路面暖光 |
| `shaders/opera.js` | 歌剧院瓷砖：亮白 / 哑光米色两种砖的人字纹，远处渐变为平均色；夜间泛光 |
| `environment.js` | Poly Haven HDRI 天空（三档时间），按 HDRI 中实测太阳位置旋转天空，使阴影方向与天空一致；3 级 CSM 阴影；雾色取天空地平线实测平均色；水面用 three.js Water + 真实法线贴图 |
| `vegetation.js` | 约 1 万棵树（OSM 实测位置 + 林地补植），四类树形，透明叶片卡片树冠，按 700 m 分块以便视锥 / 阴影剔除 |
| `lights.js` / `post.js` | 大桥灯串；HDR 泛光 + ACES 色调映射，4x MSAA |

素材全部记录在 `web/assets/ASSETS.csv`（来源、作者、许可）：Poly Haven 纹理与 HDRI（CC0）、ambientCG 草坪（CC0）、three.js 水面法线（MIT）。原始下载保存在 `assets_src/`，网页用压缩版在 `web/assets/`（约 23 MB）。

性能（本机 Intel Arc 140T，1280×800，高画质）：每帧约 300 万三角面、400–570 次绘制，前台实测 33–56 fps；同步回读测得每帧约 14–15 ms。

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

- 近处的树是叶片卡片拼成的，远看自然，走近仍能看出卡片；草坪近看缺少法线起伏。
- 立面是程序化的统一规则，标志楼（Crown、Salesforce、Quay Quarter 等）没有专门造型和立面；无招牌、无屋顶设备细节。
- 歌剧院基座为整块挤出（无台阶、无大台阶）；壳体无厚度和肋线。
- 水面是 three.js Water：无岸边白浪、无船只与尾迹；黄金时段航拍时远处海面与天空交界仍有一条偏亮的雾带。
- 场景中没有人、车、船；北侧 1:38 短坡段未单独建模；桥端以外的道路未建模。
- 高程许可证：服务元数据只写 "DFSI 2019"，Data.NSW 上该数据集标注 "License Not Specified"；NSW 政府网站默认 CC BY 4.0，Spatial Services 的框架文件写的是 CC BY 3.0 AU。当前按 "© State of New South Wales (Spatial Services)" 署名；公开发布前建议向 Spatial Services 书面确认。数据精度：水平 ±1.25 m、垂直 ±0.9 m（95% 置信）。
- 纹理仍是 JPEG（约 23 MB）；正式发布可转 KTX2 进一步减小体积和显存。

数据：© OpenStreetMap contributors（ODbL）；高程 © State of New South Wales (Spatial Services)；纹理与天空 Poly Haven / ambientCG（CC0）。均已在网页右下角署名。three.js r170（MIT）位于 `web/vendor/three/`。
