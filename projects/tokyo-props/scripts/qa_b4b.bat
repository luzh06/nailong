@echo off
set B=E:\blender\blender.exe -b --factory-startup
%B% -P D:\Cijian\scripts\qa_street.py -- cafe_only %1 --spp 128 --w 1920 --tex 4096 > D:\Cijian\logs\qa_cafe4k.log 2>&1
echo PIPE_END2
