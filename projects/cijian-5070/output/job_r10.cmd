@echo off
"D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe" -b --python-exit-code 1 -P D:\Cijian\scripts\qs_build.py -- --tag r10 --cams west,mid,main,street,steps,road,pole,sky --lights morning --res 1920 --spp 512 > "D:\Cijian\output\job_r10.log" 2>&1
echo finished > "D:\Cijian\output\job_r10.log.done"
