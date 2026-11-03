Get-CimInstance Win32_Process | Where-Object { $_.Name -in 'blender.exe','cmd.exe','python.exe' -and $_.CommandLine -like '*Cijian*' } | ForEach-Object { '{0} {1} {2}' -f $_.ProcessId, $_.CreationDate.ToString('HH:mm'), $_.CommandLine.Substring(0, [Math]::Min(110, $_.CommandLine.Length)) }
Get-ChildItem D:\Cijian\logs\qveg.*, D:\Cijian\logs\fixveg.* | ForEach-Object { '{0} {1}' -f $_.Name, $_.LastWriteTime.ToString('HH:mm') }
Get-Date -Format HH:mm
