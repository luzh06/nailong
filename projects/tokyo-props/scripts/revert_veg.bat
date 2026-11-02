@echo off
set B=E:\blender\blender.exe -b --factory-startup
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\make_decals2.py
%B% -P D:\Cijian\scripts\asset_shop.py -- sf08 tent > D:\Cijian\logs\shop_sf08_tent.log 2>&1
%B% -P D:\Cijian\scripts\qa_street.py -- veg_only v3 --spp 128 --w 1920 --tex 4096 --cams c_veg > D:\Cijian\logs\qa_veg3.log 2>&1
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\make_manifest.py
echo PIPE_END2
