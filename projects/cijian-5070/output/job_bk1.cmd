@echo off
"D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe" -b D:\Cijian\blend\qs_bk.blend --python-exit-code 1 -P D:\Cijian\scripts\qs_bk_bake.py -- --out t1 --groups stone,road_a --passes albedo,orm,normal,sunset,sunset_vis --spp 64 --scale .5 > "D:\Cijian\output\job_bk1.log" 2>&1
echo finished > "D:\Cijian\output\job_bk1.log.done"
