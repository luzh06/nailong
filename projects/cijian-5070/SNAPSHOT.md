# 完整本机工程快照

来源：`D:\Cijian`。本目录保留源工程目录结构及文件字节，用于完整备份和团队交接；原目录没有被初始化为 Git 仓库、改写、移动或清理。

## 范围

- `assets/`、`refs_web/`、素材登记表：原始素材及来源记录。
- `blend/`：全部本机 Blender 场景和历史备份，包括 `qs_bk.blend`、`qs_bk.blend1`。
- `bake/`：本机各轮烘焙结果，包括 t1、t3、t4。
- `web/`：本机网页代码、模型数据、测试结果和相关脚本。
- `pack/`：原样保存的打包目录及窗口测试入口。
- `scripts/`、`output/`：生成脚本、输出图、日志和已有运行记录。
- `tools/`、`Cijian.zip`：Blender 便携工具、安装压缩包及原始工程 ZIP。

仅排除浏览器 profile 以及可能存在的 Git 元数据、凭据文件。实际排除项、每个文件的大小与 SHA-256 均记录在 [快照清单](../../docs/snapshots/cijian-5070-2026-11-02.json)。快照包含原有脚本和日志，不等于重新执行或验收了其中的全部功能。

## 获取

需要 Git LFS。Windows 下完整工具目录含较深路径，克隆时启用当前仓库的长路径支持：

```powershell
git -c core.longpaths=true clone https://github.com/luzh06/nailong.git
cd nailong
git config core.longpaths true
git lfs pull
git lfs fsck
```

大型模型、贴图、烘焙结果、ZIP 和工具二进制文件存储于 LFS。GitHub 网页里的 LFS 指针或不含 LFS 实体的 ZIP 下载不能替代完整克隆。完整快照占用空间较大，工具目录和安装 ZIP 同时保留是本次全量归档的一部分。

## 使用与限制

- 本目录是制作机的原样快照，脚本可能仍包含 `D:\Cijian` 和制作机上的 Blender 路径。执行前先检查路径和覆盖行为。
- 可以使用已打包的 `pack/` 继续核查当前版本；本次归档没有重新运行全部脚本或重新烘焙。
- `web/profile/` 已排除，因此浏览器测试须创建自己的本机 profile。
- 新街块 `block_A.glb`、`block_B.glb` 不在这份本机源目录快照中。归档上传期间，原制作方已将模型、配套 JSON 和预览补传到 `tokyo-5070ti-blocks` 分支；它们另存于仓库的 [`projects/tokyo-blocks/`](../tokyo-blocks/) 中，并与完整快照一起提供。
- Blender、Python 及其他随附第三方工具保留原有许可证；归档行为不为这些组件或第三方素材重新指定许可证。
