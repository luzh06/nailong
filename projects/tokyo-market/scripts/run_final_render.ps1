# Full build: scene, export, render, grade, verify. Keep this file ASCII-only (PowerShell 5.1 misreads UTF-8 without BOM).
$py = "C:\Users\Lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$b = "D:\blender-5.1.0-windows-x64\blender-5.1.0-windows-x64\blender.exe"
Get-ChildItem D:\Cijian\exports | Remove-Item
Get-ChildItem D:\Cijian\previews | Remove-Item
$t = Get-Date
& $b -b --python "D:\Cijian\scripts\build_scene.py" -- | Select-String -Pattern "^STATS |^HDRI|RENDERED|Traceback|Error:|File .D:" | ForEach-Object { $_.Line }
"render elapsed s: " + [int]((Get-Date)-$t).TotalSeconds
foreach ($f in Get-ChildItem D:\Cijian\previews -Filter *.png) {
  & $py "D:\Cijian\scripts\post_grade.py" $f.FullName ($f.FullName -replace '\.png$', '.jpg') 0.55
}
& $py "D:\Cijian\scripts\compare.py" "D:\Cijian\previews\main_dusk.jpg" "D:\Cijian\reference\ref_191_dusk.jpg" "D:\Cijian\previews\compare_main_dusk_vs_191.jpg"
$files = Get-ChildItem D:\Cijian\exports -Filter *.glb | ForEach-Object FullName
& $py "D:\Cijian\scripts\verify_glb.py" @files | Out-File "D:\Cijian\exports\stats_glb.json" -Encoding utf8
$j = Get-Content "D:\Cijian\exports\stats_glb.json" -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($x in $j) { if ($x.file -match 'master') { "$($x.file) $($x.size_MB)MB tris=$($x.tris)" } }
"shop tris max: " + ($j | Where-Object { $_.file -match 'YN_shop' } | Measure-Object tris -Maximum).Maximum
& $b -b --python "D:\Cijian\scripts\03_write_registers.py" | Select-String -Pattern "^assets|Traceback" | ForEach-Object { $_.Line }
& $b -b "D:\Cijian\master_tokyo.blend" --python "D:\Cijian\scripts\check_blend.py" | Select-String -Pattern "^CHECK (camera|images)|Traceback" | ForEach-Object { $_.Line }
"DONE"
