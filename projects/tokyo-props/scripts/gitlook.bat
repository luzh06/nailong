@echo off
cd /d D:\Cijian
if not exist D:\Cijian\gitrepo (
 git clone --filter=blob:none --no-checkout https://github.com/luzh06/nailong D:\Cijian\gitrepo
)
cd /d D:\Cijian\gitrepo
git fetch --all --quiet
echo --- branches
git branch -r
echo --- main top
git ls-tree --name-only origin/main
echo --- 5070ti top
git ls-tree --name-only origin/tokyo-5070ti-blocks
echo --- 5070ti projects
git ls-tree -r --name-only origin/tokyo-5070ti-blocks | findstr /i "projects" | findstr /v /i "\.png \.jpg" | more +0 | findstr /n "." | findstr /b "[0-9]:" 
echo --- 5070fill files
git ls-tree -r --name-only origin/tokyo-5070-fill | findstr /n "." | findstr /b "[1-4][0-9]: [1-9]:"
echo --- log
git log --format="%%h %%an %%ad %%s" --date=short -3 origin/tokyo-5070ti-blocks
git log --format="%%h %%an %%ad %%s" --date=short -3 origin/tokyo-5070-fill
git log --format="%%h %%an %%ad %%s" --date=short -3 origin/main
echo --- docs
git show origin/main:README.md 2>nul | more +0
git ls-tree -r --name-only origin/main | findstr /i "AGENTS CONTRIBUTING CLAUDE.md lfsconfig gitattributes"
echo --- lfs attrs
git show origin/main:.gitattributes
echo --- accounts
git credential-manager github list 2>&1
