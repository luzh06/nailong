# 在游戏本上起独立进程，SSH 断开不影响；结束后写 .done
param([string]$name,[string]$args1)
$bl='D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe'
$log="D:\Cijian\output\job_$name.log"
$bat="D:\Cijian\output\job_$name.cmd"
Remove-Item "$log","$log.done" -ErrorAction SilentlyContinue
Set-Content -Path $bat -Encoding ASCII -Value @("@echo off","`"$bl`" $args1 > `"$log`" 2>&1","echo finished > `"$log.done`"")
$r=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine="cmd.exe /c `"$bat`""}
"started pid=$($r.ProcessId) rc=$($r.ReturnValue)"
