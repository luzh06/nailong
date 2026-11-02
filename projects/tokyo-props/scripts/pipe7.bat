@echo off
rem pipe7.bat <tag> : batch shops + props, then full-street acceptance
set B=E:\blender\blender.exe -b --factory-startup
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\make_decals2.py
for %%i in (sf03 sf04 sf05 sf06 sf07 sf08) do (
 for %%p in (shell front tent goods) do (
  echo %%i %%p
  %B% -P D:\Cijian\scripts\asset_shop.py -- %%i %%p > D:\Cijian\logs\shop_%%i_%%p.log 2>&1
 )
)
for %%i in (pr_cone pr_barrier pr_bins pr_plants pr_gasmeter pr_aircon pr_laundry pr_sign_side) do (
 echo %%i
 %B% -P D:\Cijian\scripts\asset_props.py -- %%i > D:\Cijian\logs\prop_%%i.log 2>&1
)
%B% -P D:\Cijian\scripts\qa_street.py -- full %1 --spp 200 --w 1920 > D:\Cijian\logs\qa_full.log 2>&1
D:\Cijian\tools\pyenv\Scripts\python.exe -I D:\Cijian\scripts\make_manifest.py
echo PIPE_END2
