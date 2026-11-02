@echo off
set B=E:\blender\blender.exe -b --factory-startup
%B% -P D:\Cijian\scripts\asset_gr01.py > D:\Cijian\logs\gr01.log 2>&1
%B% -P D:\Cijian\scripts\asset_sf02.py -- front > D:\Cijian\logs\sf2_front.log 2>&1
%B% -P D:\Cijian\scripts\qa_street.py -- sf %1 --spp 220 --w 1920 > D:\Cijian\logs\qa_sf2.log 2>&1
%B% -P D:\Cijian\scripts\qa_street.py -- vm %1 --spp 220 --w 1920 --cams hero,close,detail > D:\Cijian\logs\qa_vm2.log 2>&1
%B% -P D:\Cijian\scripts\qa_street.py -- sf %1 --spp 160 --w 1600 --light noon --cams hero,street,ground > D:\Cijian\logs\qa_sf2n.log 2>&1
echo PIPE_END2
