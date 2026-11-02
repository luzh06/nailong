# Launch a detached process that survives SSH loss. usage: job.ps1 -Name x -Cmd "full command line"
param([string]$Name,[string]$Cmd)
$log="D:\project\cijian\work\logs\$Name.log"
$full="cmd.exe /c `"$Cmd > $log 2>&1 & echo EXIT %ERRORLEVEL% >> $log`""
$r=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$full;CurrentDirectory='D:\project\cijian\work\work'}
"pid=$($r.ProcessId) rc=$($r.ReturnValue) log=$log"
