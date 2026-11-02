param([string]$S="blk_a.py",[string]$Tag="r1",[string]$Args2="")
$t="D:\project\cijian\work\work\tmp"; New-Item -ItemType Directory -Force $t | Out-Null
$c="set TEMP=$t&& set TMP=$t&& D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe -b --factory-startup --python-exit-code 1 -P D:\project\cijian\work\src\$S -- --tag $Tag $Args2"
& D:\project\cijian\work\src\job.ps1 -Name "$($S)_$Tag" -Cmd $c
