# bg.ps1 <name> <command...>  start detached (survives ssh drop), log to D:\Cijian\logs\<name>.log, marker <name>.done
param([string]$Name,[string]$Cmd)
$log="D:\Cijian\logs\$Name.log"; $done="D:\Cijian\logs\$Name.done"
Remove-Item $done -ErrorAction SilentlyContinue
$bat="D:\Cijian\logs\$Name.bat"
Set-Content -Path $bat -Encoding ascii -Value "@echo off`r`nchcp 65001 >nul`r`ncall $Cmd > `"$log`" 2>&1`r`necho %ERRORLEVEL% > `"$done`""
$r=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine="cmd /c `"$bat`"";CurrentDirectory='D:\Cijian'}
"pid=$($r.ProcessId) rc=$($r.ReturnValue)"
