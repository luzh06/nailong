# One quality round: rebuild C/D/E/S GLBs, assemble with qs_h1 + A/B, render the fixed QA cameras, tile a contact sheet.
# usage: powershell -File qa_round.ps1 -Tag q1 [-Blocks C,D,E,S] [-Spp 96]
param([string]$Tag = "q1", [string]$Blocks = "C,D,E,S,X", [int]$Spp = 96, [int]$Res = 1280)
$W = "D:\project\cijian\work"; $B = "D:\Cijian\tools\blender-5.2.3-windows-x64\blender.exe"; $env:TEMP = "$W\tmp"
$scr = @{ C = "blk_c.py"; D = "blk_d.py"; E = "blk_e.py"; S = "blk_s.py"; X = "blk_x.py" }
foreach ($k in $Blocks.Split(",")) {
    & $B -b --factory-startup --python-exit-code 1 -P "$W\src\$($scr[$k])" -- --tag $Tag --render 0 --export 1 > "$W\logs\${Tag}_$k.log" 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Output "BUILD FAILED $k"; Get-Content "$W\logs\${Tag}_$k.log" -Tail 8; exit 1 }
    Select-String "$W\logs\${Tag}_$k.log" -Pattern "^TRIS|^GLB|^PROPS" | ForEach-Object { "$k $($_.Line.Substring(0, [Math]::Min(110, $_.Line.Length)))" }
}
$cams = "stairs_west,street_east,aerial,q_wall,q_poles,q_ground,q_ac,q_mokuchin,q_km,q_lantern,q_sando,q_eave,q_pagoda,q_from_street"
& $B -b D:\Cijian\blend\qs_h1.blend --python-exit-code 1 -P "$W\src\assemble.py" -- --tag $Tag --cams $cams --res $Res --spp $Spp --save 1 > "$W\logs\${Tag}_asm.log" 2>&1
if ($LASTEXITCODE -ne 0) { Write-Output "ASSEMBLY FAILED"; Get-Content "$W\logs\${Tag}_asm.log" -Tail 8; exit 1 }
Select-String "$W\logs\${Tag}_asm.log" -Pattern "^RENDER|^ALLDONE" | ForEach-Object { $_.Line }
$env:PYTHONPATH = "$W\.pydeps"
& D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe "$W\src\contact.py" $Tag $cams
