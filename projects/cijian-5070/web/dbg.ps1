Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -like '*suite.ps1*' -or $_.CommandLine -like '*bench.ps1*'} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -like '*Cijian\web*' -and $_.Name -ne 'powershell.exe' -and $_.Name -ne 'cmd.exe'} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
$py='D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe'
"py exists: $(Test-Path $py)"
$srv=Start-Process $py -ArgumentList 'D:\Cijian\web\srv.py','D:\Cijian','8765' -PassThru -WindowStyle Hidden -RedirectStandardError D:\Cijian\web\results\srv_err.txt
Start-Sleep 2
"srv alive: $(-not $srv.HasExited)"
curl.exe -s -m 5 -o NUL -w "html %{http_code} %{size_download}`n" http://127.0.0.1:8765/web/test.html
curl.exe -s -m 5 -o NUL -w "three %{http_code} %{size_download}`n" http://127.0.0.1:8765/web/vendor/three.module.js
curl.exe -s -m 5 -o NUL -w "map %{http_code}`n" http://127.0.0.1:8765/web/matmap.json
curl.exe -s -m 5 -I -w "%{content_type}`n" -o NUL http://127.0.0.1:8765/web/vendor/three.module.js
Stop-Process -Id $srv.Id -Force
Get-Content D:\Cijian\web\results\srv_err.txt -Tail 4
'--- edge'
Get-Content D:\Cijian\web\results\edge_A_raw4k.txt -Tail 6
