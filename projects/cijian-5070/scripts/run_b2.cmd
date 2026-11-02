@echo off
set BL=D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe
set O=D:\Cijian\output
del %O%\b2.step 2>nul
"%BL%" -b D:\Cijian\blend\qs_bk.blend --python-exit-code 1 -P D:\Cijian\scripts\qs_bk_all.py -- --out t3 --passes albedo,orm,normal,sunset,sunset_vis --spp 64 --scale .5 --plants sunset > %O%\job_b2bake.log 2>&1
echo bake >> %O%\b2.step
"%BL%" -b D:\Cijian\blend\qs_bk.blend --python-exit-code 1 -P D:\Cijian\scripts\qs_card.py -- --dir t3 --spp 128 > %O%\job_b2card.log 2>&1
echo card >> %O%\b2.step
"%BL%" -b D:\Cijian\blend\qs_bk.blend --python-exit-code 1 -P D:\Cijian\scripts\qs_bk_export.py -- --dir t3 --lights sunset > %O%\job_b2exp.log 2>&1
echo DONE >> %O%\b2.step
