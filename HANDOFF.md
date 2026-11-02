# 交接文档（2026-11-02）

项目：悉尼港网页漫游场景。目录 `D:\project\cijian\sydney`，git 仓库，分支 `main`，尚未推送到 GitHub（`luzh06/sydney-harbour` 用本机凭据访问时返回"不存在"，需先确认仓库地址和权限）。

## 运行 / 重建
见 README.md。本地服务：
`D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe -m http.server 8770 --bind 127.0.0.1 --directory web`
重建顺序：prep_osm.py → fetch_assets.py → build_landcover.py → `blender -b --factory-startup -P scripts/build_blockout.py`

## 已完成并验证（已提交）
- 真实数据白模：OSM 建筑/海岸/道路，NSW 5 m 裸地高程，大桥与歌剧院按公开资料校准（来源见 README）。
- 真实化第一版：HDRI 三时段天空、CSM 阴影、程序化立面、地表遮罩、约 1 万棵树、夜景灯光、Draco 压缩。
- Google 实景三维混合模式（`web/src/tiles.js`，需 `web/config.local.js` 填 Key，未用真实 Key 测试）。用户认为依赖 API Key 不稳定，倾向离线方案。

## 本轮进行中（按评审意见改，代码已写，未验证）
评审意见：先做一处质量样板 = 特征楼 + 精细岸线 + 窗后空间 + 水面。
1. 地标楼 `scripts/landmarks.py`：悉尼塔、Crown、Quay Quarter、Australia Square 重建；Governor Phillip / Chifley / Salesforce 加塔冠。尺寸凭记忆，需对照照片校准。已重建 glb 成功。
2. 立面着色器重写 `web/src/shaders/facade.js`：玻璃改为物理 Fresnel（金属度不再 0.9）、窗框、窗洞进深阴影、墙面法线图（玻璃上关闭）、**室内映射**（每扇窗后有房间、灯、窗帘，远处退化为平均亮度）、风格编码改为 /16 并新增 8 金色、9 肋柱混凝土、10 竖肋玻璃。
3. 水面 `web/src/water.js`：修补 three.js Water（F0 0.3→0.02、去掉灰色叠加），按 `assets/water/shore_distance.png` 做浅深水色和岸边浪沫；distortion 3.5。
4. 岸线 `scripts/foreshore.py`：OSM 码头 186 个平台 + 518 根桩，步行区临水边 457 根栏杆柱；海堤水线湿痕/藻类（materials.js 补丁）。
5. 新材质：wharf_timber / wharf_pile / railing_metal；`fetch_assets.py` 新增 wood_planks_grey。

**下一步先做**：跑 `tools/review_shots.js`（Playwright，见文件内机位）看是否有着色器编译错误（重点 facade.js 的 struct/室内映射、water.js 字符串替换），再逐张调参。

## 尚未开始
- 近景高质量树（建议 ez-tree, MIT）替换叶片卡片树；远处保留简化版。
- 歌剧院台阶、入口、壳体厚度；渡轮与尾迹；夜景暗楼层/亮度再调。
- 地标楼尺寸校准；README 更新本轮内容。

## 注意
- 性能测量：后台窗口会被浏览器限帧到 1 fps，用 `?bench=1` 后 `window.__bench(20)`（回读像素）测真实帧耗时。
- `.pydeps/` 不入库，按 README 用 pip --target 重装（scipy 安装曾因内存失败，已改为不依赖 scipy）。
- 素材许可登记：`web/assets/ASSETS.csv`；高程数据许可证未明确，公开发布前需向 NSW Spatial Services 确认。
