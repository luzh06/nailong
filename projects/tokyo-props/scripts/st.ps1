Get-Date -Format 'HH:mm:ss'
Get-ChildItem D:\Cijian\assets\polyhaven -Recurse -File | Sort-Object LastWriteTime | Select-Object -Last 4 @{n='t';e={$_.LastWriteTime.ToString('HH:mm:ss')}},@{n='MB';e={[math]::Round($_.Length/1MB,1)}},FullName | Format-Table -AutoSize -HideTableHeaders
Get-CimInstance Win32_Process -Filter "Name='curl.exe'" | ForEach-Object { $_.CommandLine.Substring($_.CommandLine.Length-70) }
$t=Measure-Command { curl.exe -s -m 20 -o NUL -w "speed %{speed_download} code %{http_code}`n" -r 0-3000000 https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/rusty_metal_02/rusty_metal_02_diff_2k.jpg | Write-Host }
$t.TotalSeconds
