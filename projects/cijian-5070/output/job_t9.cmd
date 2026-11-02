@echo off
"D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe" -b --python-exit-code 1 -P D:\Cijian\scripts\qs_build.py -- --tag t9 --cams west,street,main --lights sunset --res 1280 --spp 96 > "D:\Cijian\output\job_t9.log" 2>&1
echo finished > "D:\Cijian\output\job_t9.log.done"
