@echo off
set B=E:\blender\blender.exe -b --factory-startup
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\thumb.py D:\Cijian\export\props\sf08_tent\textures\sf08_tent_BaseColor.png D:\Cijian\output\t_sf08tent.jpg
%B% -P D:\Cijian\scripts\qa_street.py -- veg_only %1 --spp 128 --w 1920 --tex 4096 > D:\Cijian\logs\qa_veg.log 2>&1
echo PIPE_END2
