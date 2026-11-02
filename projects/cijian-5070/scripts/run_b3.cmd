@echo off
set BL=D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe
set O=D:\Cijian\output
del %O%\b3.step 2>nul
"%BL%" -b D:\Cijian\blend\qs_bk.blend --python-exit-code 1 -P D:\Cijian\scripts\qs_bk_all.py -- --out t4 --passes albedo,orm,normal,emit,sunset,sunset_vis --spp 512 --scale 1 --plants sunset > %O%\job_b3bake.log 2>&1
echo bake >> %O%\b3.step
"%BL%" -b D:\Cijian\blend\qs_bk.blend --python-exit-code 1 -P D:\Cijian\scripts\qs_card.py -- --dir t4 --spp 256 > %O%\job_b3card.log 2>&1
echo card >> %O%\b3.step
echo DONE >> %O%\b3.step
