$root='D:\Cijian\assets'
$items=Get-Content D:\Cijian\scripts\assets.json -Raw | ConvertFrom-Json
$bad=0
foreach($i in $items){
  $url=$i[0];$rel=$i[1].Replace('/','\');$md5=$i[2]
  $p=Join-Path $root $rel
  New-Item -ItemType Directory -Force -Path (Split-Path $p) | Out-Null
  if(-not (Test-Path $p)){ curl.exe -sSL --retry 3 -A cijian-asset-fetch -o $p $url }
  $h=(Get-FileHash $p -Algorithm MD5).Hash.ToLower()
  if($h -ne $md5){ "BAD $rel"; $bad++ }
}
"done items=$($items.Count) bad=$bad"
(Get-ChildItem $root -Recurse -File | Measure-Object Length -Sum).Sum/1MB
