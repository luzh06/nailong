@echo off
set B=E:\blender\blender.exe -b --factory-startup
%B% -P D:\Cijian\scripts\asset_sf02.py -- tent > D:\Cijian\logs\sf2_tent.log 2>&1
for %%i in (sf03 sf05 sf08) do %B% -P D:\Cijian\scripts\asset_shop.py -- %%i tent > D:\Cijian\logs\shop_%%i_tent.log 2>&1
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\thumb.py D:\Cijian\export\props\sf05_tent\textures\sf05_tent_BaseColor.png D:\Cijian\output\t_sf05tent.jpg
for %%c in (c_cafe hero c_fish) do (
 echo CAM %%c
 %B% -P D:\Cijian\scripts\qa_street.py -- full %1 --spp 128 --w 1920 --tex 2048 --cams %%c > D:\Cijian\logs\qa_full_%%c.log 2>&1
)
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\make_manifest.py
echo PIPE_END2
