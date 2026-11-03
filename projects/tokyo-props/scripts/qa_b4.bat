@echo off
set B=E:\blender\blender.exe -b --factory-startup
%B% -P D:\Cijian\scripts\asset_shop.py -- sf07 front > D:\Cijian\logs\shop_sf07_front.log 2>&1
for %%c in (c_izak street) do (
 echo CAM %%c
 %B% -P D:\Cijian\scripts\qa_street.py -- full %1 --spp 128 --w 1920 --tex 2048 --cams %%c > D:\Cijian\logs\qa_full_%%c.log 2>&1
)
echo CAM c_cafe 4K
%B% -P D:\Cijian\scripts\qa_street.py -- full %1 --spp 128 --w 1920 --tex 4096 --cams c_cafe > D:\Cijian\logs\qa_full_c_cafe.log 2>&1
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\make_manifest.py
echo PIPE_END2
