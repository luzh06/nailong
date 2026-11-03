# 此间 · 本地体验服务器（Windows 自带 PowerShell，无需安装 Python/Node）。
# 只监听本机 localhost，提供本文件夹里的静态文件，并打开浏览器。关闭此窗口即停止。
param([switch]$NoBrowser,[int]$Port=0)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$mime = @{
  '.html'='text/html; charset=utf-8'; '.js'='text/javascript; charset=utf-8'; '.mjs'='text/javascript; charset=utf-8'
  '.css'='text/css; charset=utf-8'; '.json'='application/json; charset=utf-8'; '.md'='text/markdown; charset=utf-8'
  '.csv'='text/csv; charset=utf-8'; '.txt'='text/plain; charset=utf-8'; '.svg'='image/svg+xml'
  '.png'='image/png'; '.jpg'='image/jpeg'; '.jpeg'='image/jpeg'; '.webp'='image/webp'; '.wav'='audio/wav'
  '.glb'='model/gltf-binary'; '.gltf'='model/gltf+json'; '.bin'='application/octet-stream'
  '.exr'='application/octet-stream'; '.hdr'='application/octet-stream'
}

# 找一个空闲端口
$listener = $null; $bound = 0
$ports = if ($Port) { @($Port) } else { 8790..8809 }
foreach ($p in $ports) {
  $l = New-Object System.Net.HttpListener
  $l.Prefixes.Add("http://localhost:$p/")
  try { $l.Start(); $listener = $l; $bound = $p; break } catch { $l.Close() }
}
if (-not $listener) { Write-Host '端口 8790-8809 都被占用，请关闭其他程序后重试。'; Read-Host '按回车退出'; exit 1 }

$url = "http://localhost:$bound/web/index.html"
Write-Host ''
Write-Host '  此间 · 三日归途' -ForegroundColor Yellow
Write-Host "  已在 $url 启动。浏览器会自动打开；若没有，请手动复制这个地址到 Chrome / Edge。"
Write-Host '  体验期间请保持此窗口开启，关闭窗口即结束。'
Write-Host ''
if (-not $NoBrowser) { Start-Process $url }

$rootFull = [System.IO.Path]::GetFullPath($root)
$buffer = New-Object byte[] 1048576
while ($listener.IsListening) {
  try { $ctx = $listener.GetContext() } catch { break }
  $res = $ctx.Response
  try {
    $rel = [Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath.TrimStart('/'))
    if ($rel -eq '') { $rel = 'index.html' }
    $path = [System.IO.Path]::GetFullPath((Join-Path $rootFull $rel))
    # 只允许访问本文件夹内的文件
    if (-not $path.StartsWith($rootFull, [StringComparison]::OrdinalIgnoreCase) -or -not (Test-Path -LiteralPath $path -PathType Leaf)) {
      $res.StatusCode = 404; $res.Close(); continue
    }
    $ext = [System.IO.Path]::GetExtension($path).ToLowerInvariant()
    $res.ContentType = if ($mime.ContainsKey($ext)) { $mime[$ext] } else { 'application/octet-stream' }
    $res.Headers.Add('Cache-Control', 'no-cache')
    $fs = [System.IO.File]::OpenRead($path)
    try {
      $res.ContentLength64 = $fs.Length
      $out = $res.OutputStream
      while (($n = $fs.Read($buffer, 0, $buffer.Length)) -gt 0) { $out.Write($buffer, 0, $n) }
    } finally { $fs.Close() }
    $res.Close()
  } catch {
    try { $res.StatusCode = 500; $res.Close() } catch {}
  }
}
