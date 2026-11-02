@echo off
set B=E:\blender\blender.exe -b --factory-startup
%B% -P D:\Cijian\scripts\qa_street.py -- sf %1 --spp 220 --w 1920 --cams street,ground,hero > D:\Cijian\logs\qa_sf2.log 2>&1
%B% -P D:\Cijian\scripts\qa_street.py -- vm %1 --spp 220 --w 1920 --cams hero > D:\Cijian\logs\qa_vm2.log 2>&1
if not exist D:\Cijian\export\props_rejected mkdir D:\Cijian\export\props_rejected
for %%n in (sf01_front sf01_awning sf01_sign sf01_sign_side vm01) do if exist D:\Cijian\export\props\%%n move D:\Cijian\export\props\%%n D:\Cijian\export\props_rejected\ >nul
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\make_manifest.py
echo PIPE_END2
