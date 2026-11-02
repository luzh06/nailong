$w='D:\Cijian\web\bench.ps1'
Remove-Item D:\Cijian\web\results\vram.jsonl -ErrorAction SilentlyContinue
& $w -name A_raw4k -query 'name=A_raw4k&glb=/web/data/raw.glb&tex=4k&shadow=dynamic&w=1920&h=1080' *>> D:\Cijian\web\results\suite.log
& $w -name B_opt2k -query 'name=B_opt2k&glb=/web/data/opt.glb&tex=2k&shadow=dynamic&w=1920&h=1080' *>> D:\Cijian\web\results\suite.log
& $w -name C_opt2k_static -query 'name=C_opt2k_static&glb=/web/data/opt.glb&tex=2k&shadow=static&w=1920&h=1080' *>> D:\Cijian\web\results\suite.log
& $w -name D_opt2k_1440 -query 'name=D_opt2k_1440&glb=/web/data/opt.glb&tex=2k&shadow=static&w=2560&h=1440' *>> D:\Cijian\web\results\suite.log
'ALL' | Add-Content D:\Cijian\web\results\suite.log
