$ms='https://mirrors.tuna.tsinghua.edu.cn/blender/release/Blender5.2/','https://mirrors.aliyun.com/blender/release/Blender5.2/','https://ftp.nluug.nl/pub/graphics/blender/release/Blender5.2/','https://mirrors.dotsrc.org/blender/blender-release/Blender5.2/','https://mirror.clarkson.edu/blender/release/Blender5.2/'
foreach($m in $ms){
 $r = curl.exe -sSL -m 15 -o NUL -w "%{http_code} %{time_total}" ($m+'blender-5.2.3.sha256')
 "$r  $m"
 $t = curl.exe -sSL -m 15 ($m+'blender-5.2.3.sha256') | Select-String 'windows-x64.zip'
 "   $t"
}
