# 《此间 · 三日归途》上传清单（给 Codex）

> Claude 已完成打包与验证，本文只说明**传什么、传到哪里、用什么命令**。全部在 5070 本机执行。
> 公开仓库：<https://github.com/luzh06/nailong>。上传前请先告诉用户，用户确认后再推送。

## 0. 本机文件位置

| 用途 | 本机路径 | 大小 |
|---|---|---|
| 离线体验包（发给评委/朋友） | `D:\project\chatgpt\ci\output\cijian-release\此间_三日归途.zip` | 288 MB |
| 同一包的解压目录（用于网页版） | `D:\project\chatgpt\ci\output\cijian-release\此间_三日归途\` | 500 MB，566 个文件 |
| 作品截图 8 张 | `D:\project\chatgpt\ci\output\cijian-release\showcase\*.jpg` | 约 3 MB |
| 源码分支 | `D:\project\chatgpt\ci\nailong`，分支 `codex/tokyo-integration` | — |

体验包里不含 Python/Node 依赖：Windows 双击「开始体验.cmd」，用系统自带 PowerShell 起本机服务并打开浏览器。已从解压后的副本实测：495 个资源 0 失败，开场到入城约 28 秒，控制台 0 错误。
重新打包（代码有改动时）：`node projects/tokyo-world/scripts/sync_game.mjs`，再 `node projects/tokyo-world/scripts/build_release.mjs`。

## 1. 源码：推送分支（必须先做）

```powershell
cd D:\project\chatgpt\ci\nailong
git lfs push origin codex/tokyo-integration
git push -u origin codex/tokyo-integration
```

- 只推这个分支，不要合并进 main（合并前问用户）。
- 暂存区里还有 516 个 `projects/tokyo-props` 文件（另一轮留下、未提交），**不要**顺手提交。

## 2. 离线体验包：GitHub Release（下载链接，给评委和传播用）

```powershell
cd D:\project\chatgpt\ci\output\cijian-release
gh release create cijian-v1.0 "此间_三日归途.zip" showcase\01-标题.jpg showcase\02-借阅卡.jpg showcase\03-翻书入城.jpg showcase\04-夕阳台阶.jpg showcase\05-樱花树下相遇.jpg showcase\06-宝蔵门烟花.jpg showcase\07-旅行图鉴.jpg showcase\08-四人回忆卡.jpg `
  --repo luzh06/nailong --target codex/tokyo-integration `
  --title "此间 · 三日归途 v1.0（可玩版）" `
  --notes "下载 此间_三日归途.zip → 解压 → 双击「开始体验.cmd」。推荐 Chrome/Edge、独立显卡、全屏。约 10–15 分钟。"
```

- 单个附件上限 2 GB，288 MB 没问题；Release 附件不走 LFS，评委直接下载即可。
- 得到的下载地址形如 `https://github.com/luzh06/nailong/releases/download/cijian-v1.0/此间_三日归途.zip`，写进作品提交页。

## 3. 网页版：GitHub Pages（点开即玩的链接）

主仓库用了 LFS，Pages 不会提供 LFS 文件，所以**新建一个不用 LFS 的公开仓库**专门放网页：

```powershell
gh repo create luzh06/cijian-play --public --description "此间 · 三日归途（网页可玩版）"
cd D:\project\chatgpt\ci\output\cijian-release\此间_三日归途
git init -b main
git config http.postBuffer 524288000
git add -A
git commit -m "此间 · 三日归途 v1.0 网页版"
git remote add origin https://github.com/luzh06/cijian-play.git
git push -u origin main
gh api -X POST repos/luzh06/cijian-play/pages -f "source[branch]=main" -f "source[path]=/"
```

- 网址：<https://luzh06.github.io/cijian-play/>（根目录 index.html 会跳到 `web/index.html`）；首次部署约 1–3 分钟。
- 文件限制核对：最大文件 `web/data/bk.glb` 63.6 MB（< 100 MB，会有 >50 MB 的提示，可忽略）；总量约 500 MB（< Pages 1 GB）。`.nojekyll` 已放好。
- **不要**在这个新仓库里加 `.gitattributes` / LFS。
- 部署后用 Chrome 打开网址实际走一遍：选角色 → 进入东京 → 能走动、能拍照。
- 说明：网页版首次打开要下载约 430 MB，网速慢时载入会较久；评委最稳妥的是第 2 步的离线包。

备选（Pages 不可用时）：Netlify，`npx netlify-cli deploy --prod --dir "D:\project\chatgpt\ci\output\cijian-release\此间_三日归途"`。Cloudflare Pages 不可用（单文件 25 MB 上限，本作有 4 个文件超出）。

## 4. 作品提交页建议写

- 在线体验：`https://luzh06.github.io/cijian-play/`
- 离线下载：第 2 步的 Release 链接（Windows，解压后双击「开始体验.cmd」）
- 截图：`showcase/` 8 张
- 运行要求：Chrome / Edge，开启硬件加速，建议独立显卡；键鼠操作，约 10–15 分钟

## 5. 做完后回填

在本文件末尾追加：实际的 Release 链接、Pages 链接、推送的提交号、网页版实测结果（能否进城、帧数大概多少）。
