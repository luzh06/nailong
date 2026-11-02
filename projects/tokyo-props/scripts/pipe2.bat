@echo off
set B=E:\blender\blender.exe -b --factory-startup
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\make_decals.py
%B% -P D:\Cijian\scripts\asset_vm02.py > D:\Cijian\logs\vm02.log 2>&1
%B% -P D:\Cijian\scripts\qa_street.py -- vm %1 --spp 160 --w 1600 > D:\Cijian\logs\qa_vm2.log 2>&1
echo PIPE_END2
