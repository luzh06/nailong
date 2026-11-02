@echo off
set BL=D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe
set O=D:\Cijian\output
del %O%\b5.step 2>nul
del D:\Cijian\bake\t4\siding_normal.png D:\Cijian\bake\t4\siding_orm.png D:\Cijian\bake\t4\siding_sunset.exr D:\Cijian\bake\t4\siding_sunset_vis.exr 2>nul
"%BL%" -b D:\Cijian\blend\qs_bk.blend --python-exit-code 1 -P D:\Cijian\scripts\qs_bk_bake.py -- --out t4 --groups siding --passes orm,normal,sunset,sunset_vis --spp 512 --scale 1 > %O%\job_b5bake.log 2>&1
echo bake >> %O%\b5.step
"%BL%" -b --python-exit-code 1 -P D:\Cijian\scripts\qs_pack.py -- --dir t4 > %O%\job_b5pack.log 2>&1
echo DONE >> %O%\b5.step
