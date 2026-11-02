'--- git'; (Get-Command git -ErrorAction SilentlyContinue).Source; git --version 2>$null
'--- gh'; (Get-Command gh -ErrorAction SilentlyContinue).Source
'--- lfs'; git lfs version 2>$null
'--- cred helper'; git config --global credential.helper 2>$null
'--- user'; git config --global user.name 2>$null
'--- ssh keys'; Get-ChildItem $env:USERPROFILE\.ssh -Name -ErrorAction SilentlyContinue
'--- reach'; git ls-remote https://github.com/luzh06/nailong 2>&1 | Select-Object -First 5
'--- sizes (MB)'
foreach ($p in 'D:\Cijian\export\props','D:\Cijian\export\props_rejected','D:\Cijian\scripts','D:\Cijian\output\previews','D:\Cijian\assets\decals','D:\Cijian\assets\fonts','D:\Cijian\assets\polyhaven','D:\Cijian\assets\polyhaven_models','D:\Cijian\assets\plateau') {
  $f = Get-ChildItem $p -Recurse -File -ErrorAction SilentlyContinue
  '{0} {1} files {2:N0} MB, largest {3:N1} MB' -f $p, $f.Count, (($f | Measure-Object Length -Sum).Sum/1MB), (($f | Measure-Object Length -Maximum).Maximum/1MB)
}
