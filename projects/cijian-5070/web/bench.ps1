param([string]$name,[string]$query,[int]$timeout=240)
$py='D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe'
$web='D:\Cijian\web'
$edge='C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
$done="$web\results\done_$name.json"
Remove-Item "$web\results\$name*","$done" -ErrorAction SilentlyContinue
$base=[int](nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
$srv=Start-Process $py -ArgumentList "$web\srv.py",'D:\Cijian','8765' -PassThru -WindowStyle Hidden
Start-Sleep 2
$url="http://127.0.0.1:8765/web/test.html?$query"
$a=@('--headless=new','--use-angle=vulkan','--enable-features=Vulkan,DefaultANGLEVulkan,VulkanFromANGLE','--force_high_performance_gpu','--ignore-gpu-blocklist','--disable-gpu-vsync','--disable-frame-rate-limit','--disable-background-timer-throttling','--disable-renderer-backgrounding','--disable-gpu-process-crash-limit','--enable-precise-memory-info','--no-first-run',"--user-data-dir=$web\profile",'--window-size=1940,1100',"`"$url`"")
$b=Start-Process $edge -ArgumentList $a -PassThru -RedirectStandardError "$web\results\edge_$name.txt"
$peak=0;$util=0;$t=0
while($t -lt $timeout -and -not (Test-Path $done)){ Start-Sleep 1;$t++
 $r=(nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits).Split(',')
 if([int]$r[0] -gt $peak){$peak=[int]$r[0]}; if([int]$r[1] -gt $util){$util=[int]$r[1]} }
Start-Sleep 1
Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -like "*$web\profile*"} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Stop-Process -Id $srv.Id -Force -ErrorAction SilentlyContinue
"{`"name`":`"$name`",`"vramBaseMB`":$base,`"vramPeakMB`":$peak,`"gpuUtilPeak`":$util,`"seconds`":$t,`"finished`":$(if(Test-Path $done){'true'}else{'false'})}" | Add-Content "$web\results\vram.jsonl"
"$name t=$t base=$base peak=$peak util=$util"
