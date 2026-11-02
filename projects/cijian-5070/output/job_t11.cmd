@echo off
"D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe" -b --python-exit-code 1 -P D:\Cijian\scripts\qs_build.py -- --tag t11 --cams west,mid,main,street --lights morning,sunset --res 1280 --spp 128 > "D:\Cijian\output\job_t11.log" 2>&1
echo finished > "D:\Cijian\output\job_t11.log.done"
