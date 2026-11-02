# 此间：全量上传与核验报告

核验时间：2026-11-02T15:29:44.9592941+08:00
快照时间：2026-11-02T14:50:01.533117+08:00

快照时本机 D:\Cijian 中可取得的 8,420 个工程文件，共 6,115,897,381 字节（5.70 GiB），已按原始目录结构归档到 GitHub main 分支的 projects/cijian-5070/。

上传期间，原制作方补交了两个新街块模型及配套文件，已将 tokyo-5070ti-blocks 分支合入 main。两个模型不属于本机 D:\Cijian 快照，按独立来源保存于 projects/tokyo-blocks/。

- 仓库：https://github.com/luzh06/nailong
- 完整快照：https://github.com/luzh06/nailong/tree/main/projects/cijian-5070
- 归档提交：468590eff856ae62a8a3abd494bc1f693e6ba571
- 街块交付提交：2e81b30745f1b745db080857f3c139c9b10ee8c4
- 整合提交：a212ed720fc7c881fdad6115f0473c7c40c98e91
- 逐文件清单：docs/snapshots/cijian-5070-2026-11-02.json

## 已归档范围

| 目录或文件 | 源文件数 | 体积 | 内容 |
|---|---:|---:|---|
| tools | 7,175 | 1.27 GiB | Blender 便携工具及原始安装 ZIP |
| bake | 429 | 1.25 GiB | t1、t3、t4 等各轮烘焙结果 |
| assets | 221 | 1.09 GiB | 模型、贴图、HDRI 与其他素材 |
| blend | 19 | 884.3 MiB | 全部本机场景和历史备份 |
| Cijian.zip | 1 | 590.9 MiB | 原始工程压缩包 |
| pack | 225 | 454.6 MiB | 原样打包目录及窗口测试入口 |
| web | 111 | 169.4 MiB | 网页、模型数据、脚本及测试结果 |
| output | 201 | 32.4 MiB | 已有输出、图片和作业记录 |
| refs_web | 3 | 11.4 MiB | 参考图 |
| scripts | 34 | 213.9 KiB | 生成、烘焙和整理脚本 |
| asset-register.csv | 1 | 10.9 KiB | 素材来源及许可登记 |

## 核验结果

- 源目录、快照清单与复制文件集合一致：8,420 / 8,420。
- 源文件和副本逐文件 SHA-256、大小核对：无差异。
- 已提交快照共 8,421 个文件，其中额外 1 个为 SNAPSHOT.md 说明；普通 Git 内容与 LFS 指针的哈希和大小均已核对。
- 快照中 1,515 个文件使用 LFS；本地 git lfs fsck 通过。
- main 分支共 1,930 条 LFS 文件路径，对应 1,583 个去重对象；LFS download batch API 返回 1,583 个对象全部可用，缺失 0。未重新下载全部 LFS 实体。
- 两份新增 GLB 的文件大小与 SHA-256 均匹配 LFS 指针；GLB 版本 2 和头部长度检查通过。
- 本次归档与街块交付两个提交均是整合提交的祖先；快照原文件保持不变。最终报告和获取说明另行提交。
- 首次整理原型及队友原分支均保留，没有改写其历史。

## 排除项与模型补齐

- 排除 web/profile/：浏览器 Cookie、登录数据和缓存不纳入项目仓库。
- block_A.glb（55,399,824 字节）和 block_B.glb（49,266,708 字节）已由队友补传，并合入主分支。
- 配套统计、建筑与接口数据、锚点、预览及生成脚本一并保留；本次已知来源范围内没有尚待补传的项目交付文件。
- 新街块尚未烘焙，也未完成 Three.js 集成；上传完成不表示完整游玩流程完成。
- 原始 ZIP 已检查目录清单，未发现浏览器资料或命名凭据文件路径。

## 获取完整文件

需要 Git LFS。Windows 克隆时启用仓库长路径支持：

```powershell
git -c core.longpaths=true clone https://github.com/luzh06/nailong.git
cd nailong
git config core.longpaths true
git lfs pull
git lfs fsck
```

GitHub 网页的 LFS 指针或不含 LFS 实体的 ZIP 下载不能替代完整克隆。

## 使用边界

原制作目录未修改，运行中的 Blender 未停止。历史文件、日志、工具安装包和解压目录均按全量要求保留。原脚本可能包含制作机绝对路径，执行前先检查路径和覆盖行为。此次归档和上传核验不代表重新烘焙、功能或画质验收。第三方工具与素材继续适用各自原许可证。
