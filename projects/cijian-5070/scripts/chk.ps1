Get-Date
'--- processes'
Get-Process | Where-Object { $_.ProcessName -like '*blender*' } | Select-Object Id,ProcessName,StartTime | Format-Table -AutoSize
'--- app errors last 3h'
Get-WinEvent -FilterHashtable @{LogName='Application';StartTime=(Get-Date).AddHours(-3);Id=1000,1001,1002} -ErrorAction SilentlyContinue | Where-Object { $_.Message -match 'blender' } | Select-Object TimeCreated,Id,@{n='m';e={$_.Message.Substring(0,[Math]::Min(300,$_.Message.Length))}} | Format-List
'--- gpu driver resets (TDR) last 3h'
Get-WinEvent -FilterHashtable @{LogName='System';StartTime=(Get-Date).AddHours(-3);ProviderName='Display','nvlddmkm'} -ErrorAction SilentlyContinue | Select-Object TimeCreated,Id,ProviderName | Format-Table -AutoSize
'--- logon sessions'
query user 2>$null
'--- blender crash files'
Get-ChildItem $env:TEMP -Filter *.crash.txt -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name,LastWriteTime | Format-Table -AutoSize
Get-ChildItem $env:TEMP -Filter quit.blend -ErrorAction SilentlyContinue | Select-Object Name,LastWriteTime,Length | Format-Table -AutoSize
'--- nvidia'
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader
