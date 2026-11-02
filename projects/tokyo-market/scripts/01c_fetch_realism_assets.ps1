# Fetch the CC0 assets with PowerShell because Python downloads get connection resets. Existing files are skipped. Keep ASCII-only.
$ErrorActionPreference = 'Stop'
$root = 'D:\Cijian'
$h = @{ 'User-Agent' = 'Cijian-project/0.1' }
New-Item -ItemType Directory -Force "$root\hdri" | Out-Null
$hdris = @{ morning = 'kloppenheim_06_puresky'; sunset = 'belfast_sunset_puresky'; dusk = 'qwantani_dusk_2_puresky' }
$walls = @{ plaster = 'white_plaster_rough_01'; concrete = 'concrete_wall_006'; tile = 'rectangular_facade_tiles'; brick = 'red_brick_03'; paint = 'painted_concrete' }
function Get-Try($url, $out) {
  if ($out -and (Test-Path $out) -and (Get-Item $out).Length -gt 0) { return }
  for ($i = 0; $i -lt 5; $i++) {
    try {
      if ($out) { Invoke-WebRequest $url -Headers $h -OutFile $out -UseBasicParsing -TimeoutSec 300; return }
      return Invoke-RestMethod $url -Headers $h -TimeoutSec 60
    } catch { Write-Output "retry $i $url"; Start-Sleep -Seconds 15 }
  }
  throw "failed $url"
}
foreach ($k in $hdris.Keys) {
  $f = Get-Try "https://api.polyhaven.com/files/$($hdris[$k])" $null
  Get-Try $f.hdri.'8k'.hdr.url "$root\hdri\$k.hdr"
  Write-Output "$k $([math]::Round((Get-Item "$root\hdri\$k.hdr").Length/1MB,1)) MB"
}
foreach ($k in $walls.Keys) {
  $f = Get-Try "https://api.polyhaven.com/files/$($walls[$k])" $null
  Get-Try $f.Diffuse.'2k'.jpg.url "$root\textures\wall_${k}_diff_2k.jpg"
  Get-Try $f.nor_gl.'2k'.jpg.url "$root\textures\wall_${k}_nor_gl_2k.jpg"
  Get-Try $f.arm.'2k'.jpg.url "$root\textures\wall_${k}_arm_2k.jpg"
  Write-Output "$k ok"
}
