@echo off
del D:\Cijian\output\b4.step 2>nul
D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe -b D:\Cijian\blend\qs_bk.blend --python-exit-code 1 -P D:\Cijian\scripts\qs_probe.py -- --dir t4 > D:\Cijian\output\job_probe.log 2>&1
echo DONE >> D:\Cijian\output\b4.step
