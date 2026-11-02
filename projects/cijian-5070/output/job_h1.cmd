@echo off
"D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe" -b --python-exit-code 1 -P D:\Cijian\scripts\qs_build.py -- --tag h1 --cams west --lights sunset --res 2560 --spp 768 > "D:\Cijian\output\job_h1.log" 2>&1
echo finished > "D:\Cijian\output\job_h1.log.done"
