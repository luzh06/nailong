$dirs='C:\ProgramData\Microsoft\Windows\WER\ReportArchive','C:\ProgramData\Microsoft\Windows\WER\ReportQueue',"$env:LOCALAPPDATA\Microsoft\Windows\WER\ReportArchive","$env:LOCALAPPDATA\Microsoft\Windows\WER\ReportQueue"
foreach($d in $dirs){ if(Test-Path $d){ Get-ChildItem $d -Directory -ErrorAction SilentlyContinue | Where-Object {$_.Name -match 'blender' -and $_.LastWriteTime -gt (Get-Date).AddHours(-4)} | Sort-Object LastWriteTime | ForEach-Object {
  $w=Join-Path $_.FullName 'Report.wer'
  if(Test-Path $w){ $t=Get-Content $w -Encoding Unicode; $p=($t | Select-String '^AppPath=|^OriginalFilename=|^TargetAppId=').Line -join ' | '; "$($_.LastWriteTime.ToString('HH:mm:ss')) $p" } } } }
'--- temp blends'
Get-ChildItem $env:TEMP -Filter *.blend -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 6 Name,LastWriteTime,Length | Format-Table -AutoSize
'--- my runs end times'
Get-ChildItem D:\Cijian\output\log_*.txt | Select-Object Name,LastWriteTime | Format-Table -AutoSize
