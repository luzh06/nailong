@echo off
del D:\Cijian\output\b5.step 2>nul
D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe -b --python-exit-code 1 -P D:\Cijian\scripts\qs_pack.py -- --dir t4 > D:\Cijian\output\job_b5pack.log 2>&1
echo DONE >> D:\Cijian\output\b5.step
