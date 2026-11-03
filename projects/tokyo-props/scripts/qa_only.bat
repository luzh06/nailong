@echo off
set B=E:\blender\blender.exe -b --factory-startup
%B% -P D:\Cijian\scripts\qa_street.py -- sf %1 --spp 160 --w 1600 > D:\Cijian\logs\qa_sf2.log 2>&1
%B% -P D:\Cijian\scripts\qa_street.py -- vm %1 --spp 160 --w 1600 --cams hero,close,detail > D:\Cijian\logs\qa_vm2.log 2>&1
echo PIPE_END2
