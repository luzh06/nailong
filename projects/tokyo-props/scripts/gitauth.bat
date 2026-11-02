@echo off
cd /d D:\Cijian\gitrepo
set GCM_INTERACTIVE=never
set GIT_TERMINAL_PROMPT=0
set GIT_LFS_SKIP_SMUDGE=1
if exist .git\index.lock del .git\index.lock
git sparse-checkout init --no-cone
git sparse-checkout set "/*" "!/*/" "/projects/tokyo-props/"
git checkout -q -f -B tokyo-5060-props origin/main 2>&1
echo checkout_rc=%ERRORLEVEL%
dir /b
git push --dry-run origin tokyo-5060-props 2>&1
echo push_rc=%ERRORLEVEL%
