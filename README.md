# 此间 Cijian

沉浸式文化旅行项目。此仓库从现有本机成果整理而来，当前版本提供两套场景原型、美术资产、生成脚本与运行证据，供三人团队继续整合。

**当前阶段：场景资产与网页技术预览。** 商店街预览和台阶优化模型测试已运行；人物对话、任务选择、玩家拍照、回忆卡与续玩尚未形成完整流程。源码仓库不是已上线游戏。

[阅读文件审查 PDF](docs/reports/此间_项目文件审查报告_2026-11-02.pdf) · [查看文字版审查](docs/reports/2026-11-02-audit.md)

完整本机工程快照位于 [`projects/cijian-5070/`](projects/cijian-5070/)，包含原始目录结构、历史场景、各轮烘焙、打包版本、原始 ZIP 和 Blender 工具。快照范围、获取方式及外部街块模型的独立来源见 [快照说明](projects/cijian-5070/SNAPSHOT.md)，逐文件校验值见 [完整清单](docs/snapshots/cijian-5070-2026-11-02.json)。

[全量上传核验 PDF](docs/reports/此间_全量上传核验报告_2026-11-02.pdf) · [全量上传文字报告](docs/reports/2026-11-02-full-upload.md)。街块 A、B 的模型及配套文件已补齐并合入主分支，见 [`projects/tokyo-blocks/`](projects/tokyo-blocks/)。

## 目录

| 路径 | 内容 |
|---|---|
| `projects/tokyo-market/` | 从原 `Cijian.zip` 整理的商店街原型：网页、模块化店铺与地标、人群、Blender 场景、纹理及来源记录 |
| `projects/yuyake-dandan/` | 台阶与街巷质量样板：已完成 h1 场景、代表渲染图、生成脚本、raw/opt 模型与性能测试页 |
| `projects/cijian-5070/` | `D:\Cijian` 完整本机快照；包含工具、历史文件、烘焙与 pack，保留源文件字节 |
| `projects/tokyo-blocks/` | 按 PLATEAU 真实路网生成的两个街块：GLB、预览、接口坐标、店面预留位与生成脚本；地点未定，未烘焙 |
| `docs/context/` | 团队提供的需求、两日规划与 Agent 手册原文；其中建议不等于已经确认或实现 |
| `docs/reports/` | 文件审查、实际运行截图和核验数据；PDF 报告与 Markdown 结论相互补充 |
| `docs/snapshot-manifest.json` | 原文件来源、快照时间、每个导入文件的大小与 SHA-256 |

首次整理的两套原型保留原有归档范围；新增的完整本机快照另外保存历史场景、烘焙输出、工具和日志。原制作目录及运行中的进程未被修改或停止。浏览器 profile 中的登录数据、Cookie 和缓存不纳入仓库；快照包含某个文件不代表该文件已通过功能或画质验收。

## 获取完整资源

模型、纹理、天空图和大体积嵌入场景数据采用 Git LFS。协作者需要 Git 和 Git LFS：

```powershell
git -c core.longpaths=true clone https://github.com/luzh06/nailong.git
cd nailong
git config core.longpaths true
git lfs pull
```

GitHub 的“Download ZIP”是否包含 LFS 实体取决于仓库设置；本项目以 `git clone` 加 `git lfs pull` 为准。不要把 LFS 指针文件当作实际模型或图片。

## 打开商店街预览

已核验浏览器：Windows Edge。需有 Python 3，以及能访问 jsDelivr 的网络；当前网页使用 Three.js 0.160.0 的 CDN。

在仓库根目录运行：

```powershell
python -m http.server 8765 --bind 127.0.0.1 --directory .\projects\tokyo-market\web
```

浏览器打开 <http://127.0.0.1:8765/>。WASD 行走，按住鼠标拖动环视，Shift 快走。界面支持早晨/日落/蓝调、步行/主机位、行人显示。人群目前是静态装饰。

在原制作电脑上，若 `python` 只是 Windows 应用商店别名，可用已存在的 Blender 自带 Python 替换命令开头：

```powershell
& 'D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe' -m http.server 8765 --bind 127.0.0.1 --directory .\projects\tokyo-market\web
```

## 打开台阶优化模型测试

该入口是自动走镜头和测帧工具，不是玩家游玩流程。在仓库根目录执行：

```powershell
python .\projects\yuyake-dandan\web\srv.py "$PWD\projects\yuyake-dandan" 8766
```

浏览器打开：

<http://127.0.0.1:8766/web/test.html?name=local_opt&glb=/web/data/opt.glb&tex=2k&shadow=static&w=1280&h=720&frames=900>

测试结束后，结果写入对应项目的 `web/results/`；这些本机结果不纳入 Git。关闭服务终端或按 Ctrl+C 停止本次服务。`srv.py` 仅是原工程的本机调试工具，不用作公开服务器。

## 编辑与继续制作

- 商店街：打开 `projects/tokyo-market/master_tokyo.blend`；脚本大多按自身目录定位资源。
- 台阶质量样板：打开 `projects/yuyake-dandan/blend/qs_h1.blend`。该场景及导入脚本仍保留原 `D:\Cijian` 资源路径；在其他电脑重建前，先重定位资产或调整 `ROOT`，不要直接运行并覆盖原工程。
- 已有 GLB 与渲染图属于各自历史输出；当前生成脚本按本次快照保存，未声称逐字节重建历史文件。
- 两套原型尚未统一。当前文件夹使用 Three.js r170，商店街预览使用 r160；地点内容、坐标朝向、材质和状态都需要明确整合。

下一步建议：完成烘焙与资源映射 → 确定主工程和真实地点 → 打通一次文化互动、选择、真实拍照与回忆卡 → 接入状态、续玩、天气、声音 → 试玩与部署。

## 素材与许可

两套项目分别保留 `asset-register.csv`、来源 JSON、参考笔记与字体许可证。第三方素材按各自记录管理，发布前完善最终致谢与许可核验。本仓库没有为所有源码或第三方资产统一指定新的开源许可证。
