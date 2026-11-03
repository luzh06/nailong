@echo off
cd /d "%~dp0"
if exist "D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe" (
  "D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe" serve.py --open
) else (
  py -3 serve.py --open
)
pause
