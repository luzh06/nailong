@echo off
set B=E:\blender\blender.exe -b --factory-startup
copy /y D:\Cijian\output\previews\v1\veg_only_c_veg_sunset.jpg D:\Cijian\output\previews\v1\before_c_veg.jpg >nul
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\make_decals2.py
%B% -P D:\Cijian\scripts\asset_shop.py -- sf08 tent > D:\Cijian\logs\shop_sf08_tent.log 2>&1
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\thumb.py D:\Cijian\export\props\sf08_tent\textures\sf08_tent_BaseColor.png D:\Cijian\output\t_sf08tent2.jpg
%B% -P D:\Cijian\scripts\qa_street.py -- veg_only v2 --spp 128 --w 1920 --tex 4096 > D:\Cijian\logs\qa_veg2.log 2>&1
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\make_manifest.py
echo PIPE_END2
