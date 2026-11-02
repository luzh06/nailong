Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'git*' } | ForEach-Object { '{0} {1}' -f $_.ProcessId, $_.CommandLine.Substring(0, [Math]::Min(120, $_.CommandLine.Length)) }
'{0:N0} MB in gitrepo' -f ((Get-ChildItem D:\Cijian\gitrepo -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum / 1MB)
