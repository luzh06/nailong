@echo off
set BL=D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe
set O=D:\Cijian\output
del %O%\b4.step 2>nul
"%BL%" -b D:\Cijian\blend\qs_bk.blend --python-exit-code 1 -P D:\Cijian\scripts\qs_bk_export.py -- --dir t4 --lights sunset > %O%\job_b4exp.log 2>&1
echo DONE >> %O%\b4.step
