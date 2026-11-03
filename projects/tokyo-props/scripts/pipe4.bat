@echo off
rem pipe4.bat <tag> : rebuild everything, then street acceptance
set B=E:\blender\blender.exe -b --factory-startup
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\make_decals.py
echo GR
%B% -P D:\Cijian\scripts\asset_gr01.py > D:\Cijian\logs\gr01.log 2>&1
echo VM
%B% -P D:\Cijian\scripts\asset_vm02.py > D:\Cijian\logs\vm02.log 2>&1
for %%s in (shell front goods) do (
 echo SF %%s
 %B% -P D:\Cijian\scripts\asset_sf02.py -- %%s > D:\Cijian\logs\sf2_%%s.log 2>&1
)
%B% -P D:\Cijian\scripts\qa_street.py -- sf %1 --spp 180 --w 1600 > D:\Cijian\logs\qa_sf2.log 2>&1
%B% -P D:\Cijian\scripts\qa_street.py -- vm %1 --spp 180 --w 1600 --cams hero,close,detail > D:\Cijian\logs\qa_vm2.log 2>&1
echo PIPE_END2
