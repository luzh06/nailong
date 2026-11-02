@echo off
echo begin > D:\Cijian\output\b1.begin
set BL=D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe
set O=D:\Cijian\output
del %O%\b1.step 2>nul
"%BL%" -b --python-exit-code 1 -P D:\Cijian\scripts\qs_build.py -- --tag b1 --cams steps,pole --lights sunset --res 1920 --spp 256 > %O%\job_b1.log 2>&1
echo build >> %O%\b1.step
"%BL%" -b D:\Cijian\blend\qs_b1.blend --python-exit-code 1 -P D:\Cijian\scripts\qs_bk_prep.py > %O%\job_b1prep.log 2>&1
echo prep >> %O%\b1.step
"%BL%" -b D:\Cijian\blend\qs_bk.blend --python-exit-code 1 -P D:\Cijian\scripts\qs_bk_all.py -- --out t3 --passes albedo,orm,normal,sunset,sunset_vis --spp 64 --scale .5 --plants sunset > %O%\job_b1bake.log 2>&1
echo bake >> %O%\b1.step
"%BL%" -b D:\Cijian\blend\qs_bk.blend --python-exit-code 1 -P D:\Cijian\scripts\qs_bk_export.py -- --dir t3 --lights sunset > %O%\job_b1exp.log 2>&1
echo DONE >> %O%\b1.step
