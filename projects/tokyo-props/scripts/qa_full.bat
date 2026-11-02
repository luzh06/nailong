@echo off
rem one process per camera; close views get 2K maps, wide views 1K (8 GB card)
set B=E:\blender\blender.exe -b --factory-startup
if not "%2"=="norebuild" (
 %B% -P D:\Cijian\scripts\asset_shop.py -- sf07 front > D:\Cijian\logs\shop_sf07_front.log 2>&1
 %B% -P D:\Cijian\scripts\asset_shop.py -- sf03 goods > D:\Cijian\logs\shop_sf03_goods.log 2>&1
)
for %%c in (street east north) do (
 echo CAM %%c
 %B% -P D:\Cijian\scripts\qa_street.py -- full %1 --spp 128 --w 1920 --tex 1024 --cams %%c > D:\Cijian\logs\qa_full_%%c.log 2>&1
)
for %%c in (hero c_fish c_izak c_cafe) do (
 echo CAM %%c
 %B% -P D:\Cijian\scripts\qa_street.py -- full %1 --spp 128 --w 1920 --tex 2048 --cams %%c > D:\Cijian\logs\qa_full_%%c.log 2>&1
)
echo PIPE_END2
