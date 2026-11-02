# start a .cmd detached from SSH
param([string]$cmd)
$r=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine="cmd.exe /c `"$cmd`""}
"started pid=$($r.ProcessId) rc=$($r.ReturnValue)"
