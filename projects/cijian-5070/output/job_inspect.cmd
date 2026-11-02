@echo off
"D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe" -b D:\Cijian\blend\qs_h1.blend --python-exit-code 1 -P D:\Cijian\scripts\qs_inspect.py > "D:\Cijian\output\job_inspect.log" 2>&1
echo finished > "D:\Cijian\output\job_inspect.log.done"
