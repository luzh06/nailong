@echo off
rem pipe3.bat <tag> : shop pieces + vending machine, then street acceptance
set B=E:\blender\blender.exe -b --factory-startup
:w
if exist D:\Cijian\logs\ph_models.done goto go
ping -n 11 127.0.0.1 >nul
goto w
:go
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\make_decals.py
echo VM
%B% -P D:\Cijian\scripts\asset_vm02.py > D:\Cijian\logs\vm02.log 2>&1
for %%s in (shell front tent goods) do (
 echo SF %%s
 %B% -P D:\Cijian\scripts\asset_sf02.py -- %%s > D:\Cijian\logs\sf2_%%s.log 2>&1
)
%B% -P D:\Cijian\scripts\qa_street.py -- sf %1 --spp 160 --w 1600 > D:\Cijian\logs\qa_sf2.log 2>&1
%B% -P D:\Cijian\scripts\qa_street.py -- vm %1 --spp 160 --w 1600 > D:\Cijian\logs\qa_vm2.log 2>&1
echo PIPE_END2
