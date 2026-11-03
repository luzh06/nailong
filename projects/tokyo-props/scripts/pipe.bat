@echo off
rem pipe.bat <tag>  : build all samples then render QA from the exported GLBs
set B=E:\blender\blender.exe -b --factory-startup
:w
goto go
ping -n 11 127.0.0.1 >nul
goto w
:go
echo DECALS
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\make_decals.py
echo VM
%B% -P D:\Cijian\scripts\asset_vm01.py > D:\Cijian\logs\vm01.log 2>&1
echo BIKE
%B% -P D:\Cijian\scripts\asset_bike01.py > D:\Cijian\logs\bike01.log 2>&1
for %%s in (front awning sign sign_side) do (
 echo SF %%s
 %B% -P D:\Cijian\scripts\asset_sf01.py -- %%s > D:\Cijian\logs\sf_%%s.log 2>&1
)
%B% -P D:\Cijian\scripts\qa_render.py -- vm01 %1 > D:\Cijian\logs\qa_vm.log 2>&1
%B% -P D:\Cijian\scripts\qa_render.py -- bike01 %1 > D:\Cijian\logs\qa_bike.log 2>&1
%B% -P D:\Cijian\scripts\qa_render.py -- sf01_front,sf01_awning,sf01_sign,sf01_sign_side %1 --out sf01 > D:\Cijian\logs\qa_sf.log 2>&1
%B% -P D:\Cijian\scripts\qa_render.py -- vm01 %1_lod2 --lod 2 --cams hero --spp 48 > D:\Cijian\logs\qa_l1.log 2>&1
%B% -P D:\Cijian\scripts\qa_render.py -- bike01 %1_lod2 --lod 2 --cams hero --spp 48 > D:\Cijian\logs\qa_l2.log 2>&1
%B% -P D:\Cijian\scripts\qa_render.py -- sf01_front,sf01_awning,sf01_sign,sf01_sign_side %1_lod2 --out sf01 --lod 2 --cams hero --spp 48 > D:\Cijian\logs\qa_l3.log 2>&1
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\make_manifest.py
echo PIPE_END2
