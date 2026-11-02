param([string]$S="blk_a.py",[string]$Tag="r1",[string]$Args2="")
$t="D:\Cijian\work\tmp"; New-Item -ItemType Directory -Force $t | Out-Null
$c="set TEMP=$t&& set TMP=$t&& D:\Blender\blender.exe -b --factory-startup --python-exit-code 1 -P D:\Cijian\src\$S -- --tag $Tag $Args2"
& D:\Cijian\src\job.ps1 -Name "$($S)_$Tag" -Cmd $c
