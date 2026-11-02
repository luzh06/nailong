param([string]$page='probe.html',[int]$secs=20,[string]$angle='d3d11')
$py='D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe'
$web='D:\Cijian\web'
$edge=@('C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe','C:\Program Files\Google\Chrome\Application\chrome.exe') | Where-Object {Test-Path $_} | Select-Object -First 1
"browser: $edge"
$srv=Start-Process $py -ArgumentList "$web\srv.py",$web,'8765' -PassThru -WindowStyle Hidden
Start-Sleep 2
$a=@('--headless=new',"--use-angle=$angle",'--enable-features=Vulkan,DefaultANGLEVulkan,VulkanFromANGLE','--force_high_performance_gpu','--ignore-gpu-blocklist','--enable-unsafe-webgpu','--disable-gpu-vsync','--disable-frame-rate-limit','--disable-background-timer-throttling','--disable-renderer-backgrounding','--enable-precise-memory-info','--no-first-run',"--user-data-dir=$web\profile",'--window-size=1920,1080',"http://127.0.0.1:8765/$page")
$b=Start-Process $edge -ArgumentList $a -PassThru
Start-Sleep $secs
Stop-Process -Id $b.Id -Force -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -like "*$web\profile*"} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Stop-Process -Id $srv.Id -Force -ErrorAction SilentlyContinue
