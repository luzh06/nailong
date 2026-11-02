@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Cijian\web\gshot.ps1 -name p1 -root D:\Cijian\pack -timeout 200 -query "shots=west,mid,main,steps,road,pole,sky&w=1920&h=1080" > D:\Cijian\web\results\p1.run.txt 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Cijian\web\gshot.ps1 -name b1 -root D:\Cijian\pack -timeout 200 -query "bench=1&w=1920&h=1080&frames=900" > D:\Cijian\web\results\b1.run.txt 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Cijian\web\gshot.ps1 -name b2 -root D:\Cijian\pack -timeout 200 -query "bench=1&w=2560&h=1440&frames=900" > D:\Cijian\web\results\b2.run.txt 2>&1
echo done > D:\Cijian\web\results\fin_pb.txt
