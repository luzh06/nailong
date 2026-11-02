@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Cijian\web\gshot.ps1 -name s5 -timeout 150 -query "shots=west,mid,main,steps,road,pole,sky&w=1920&h=1080" > D:\Cijian\web\results\s5.run.txt 2>&1
echo done > D:\Cijian\web\results\fin_s5.txt
