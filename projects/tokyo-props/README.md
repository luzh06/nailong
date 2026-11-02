# tokyo-props：店面与街道道具（5060 制作）

谷中候选商店街用的店面立面、门前货物、贩卖机、自行车、路面和后巷杂物。全部在 RTX 5060 笔记本上用 Blender 5.0.1 生成、烘焙并导出为 GLB，并在真实比例的街道里、日落低角度光加空气雾的条件下验收。地点仍是候选，没有写死“谷中”。

## 目录

| 路径 | 内容 |
|---|---|
| `props/` | 交付件：36 个 GLB，每个带 LOD0/1/2 和 `_COL` 碰撞体；`textures/` 是烘焙贴图（BaseColor / Normal / ORM，发光件另有 Emissive），4K 件另附 `textures_2k/`；每件一个 JSON 说明 |
| `props/manifest.csv` | 清单：文件名、各级三角面数、贴图尺寸、尺寸、体积、来源 |
| `props/LICENSES.md` | 来源与许可 |
| `props/REVIEW*.md` | 每轮评审记录（每轮写最差三问题） |
| `previews/` | 全部评审轮次的渲染图（r1–r4 第一版，a1–a4 第二版，b2–b5 整街批量，v1–v3 八百政雨棚核对） |
| `scripts/` | 生成、烘焙、验收脚本（见下文“重新生成”） |
| `decals/` | 程序绘制的招牌、标签、暖帘、雨棚图案（原创，店名品牌均虚构） |
| `data/` | PLATEAU 取到的沿街开间与楼高统计、文件索引；素材来源登记 |
| `rejected_v1/` | 被否决的第一版（sf01 店面、vm01 贩卖机），只作留档 |

## 交付件

| 名称 | 说明 |
|---|---|
| `sf02_*` | 三径茶舗：两层，开间 5.4 m；shell（二层立面）/ front（一层）/ tent（PVC 雨棚）/ goods（门前货物） |
| `sf03_*` | 鮮魚 魚辰：瓦楞铁皮招牌，冰床鱼摊，粉色雨棚 |
| `sf04_*` | 荒物 木村：木板外墙、瓦檐、木格子门（无雨棚） |
| `sf05_*` | 喫茶 ひより：三层瓷砖楼、突出式灯箱、木框玻璃门 |
| `sf06_*` | 空店铺：卷帘门半落、阳台晾衣（无雨棚） |
| `sf07_*` | やきとり とり源：深色木板、红灯笼、门内吧台（无雨棚） |
| `sf08_*` | 青果 八百政：绿色铁皮招牌、蔬果阶梯货架、绿白条雨棚 |
| `vm02` | 自动贩卖机（虚构品牌 そよかぜ），按实拍比例 |
| `bike01` | 无品牌ママチャリ |
| `gr01_road` | 8 × 4.6 m 路面段：沥青、直边补丁、灌缝、混凝土散水、水沟盖、井盖、积水；沿 X 平铺，隔段镜像 |
| `pr_*` | 雪糕筒、A 字路障、回收箱、盆栽架、燃气表与管线、空调外机、晾衣架、灯箱招牌 |

## 坐标约定

- 1 单位 = 1 米，glTF 标准 Y 向上（Blender 中 Z 向上）。
- 店面四块（shell / front / tent / goods）共用一个原点：地面、墙线中点；街道在 -Y 方向。同一家店的四块都放在同一位置即可拼合。北侧店铺绕 Z 转 180°。
- 墙挂件（`pr_gasmeter`、`pr_aircon`、`pr_sign_side`）原点在墙线上。
- 整街示范布局见 `scripts/street_cfg.json` 的 `full` 一项（街宽 4.6 m，南北两侧各约 10 家店）。

## 验收方式与结论

- 验收脚本 `scripts/qa_street.py`：导入 GLB（不是源文件）放进真实比例街道，Cycles 渲染。整街时 8 GB 显卡装不下全部 4K 贴图，所以验收渲染把贴图限制到 1K–2K，交付文件本身仍是 4K/2K。
- 真实参考：Wikimedia Commons 谷中实拍（只看，不入库）；尺寸来自国土交通省 PLATEAU 官方 MCP 接口取得的台东区 2025 CityGML（沿街开间约 4–7 m、楼高约 7–10 m，街线为估计坐标，只作量级参考）。
- 评审记录：第一版 R1–R4（被否决）→ 第二版 A1–A4 → 整街批量 B2–B5，详见 `props/REVIEW*.md`。

## 已知问题

1. 雨棚两侧三角布与支架在贴图里占比很小，近看偏糊。
2. 7 种立面在整街里重复摆放，沿街走能认出。
3. 体积大：全部交付约 1 GB，`sf02_goods` 一件约 27 MB（扫描盆栽）。
4. 未在 Three.js 中实测；批量件的 LOD2 远景未逐个抽查。

## 重新生成

在装有 Blender 的 Windows 机器上，脚本默认根目录 `D:\Cijian`，需先下载 Poly Haven 贴图与模型（`scripts/ph_fetch.py all`、`scripts/ph_models_fetch.py`）和 OFL 字体，再运行：

```bat
blender -b --factory-startup -P scripts\asset_shop.py -- sf03 shell
blender -b --factory-startup -P scripts\asset_props.py -- pr_cone
blender -b --factory-startup -P scripts\qa_street.py -- full TAG --spp 128 --w 1920 --tex 1024 --cams street
```

## 来源与许可

- 贴图、HDRI、扫描模型：Poly Haven，CC0。
- 字体：Shippori Mincho、Yuji Syuku、Zen Kaku Gothic New、Reggae One、DotGothic16、Kaisei Opti，SIL OFL 1.1（字体文件不入库，只用于生成 `decals/` 图案）。
- 招牌、标签、暖帘等图案：本项目原创，店名、品牌、电话均虚构。
- 尺寸参考：PLATEAU（国土交通省），只用了统计数字，不含原始数据。
- 实拍参考：Wikimedia Commons（CC BY / CC BY-SA），只作参考，未用作贴图，不入库。
