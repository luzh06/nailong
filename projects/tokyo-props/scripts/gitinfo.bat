@echo off
cd /d D:\Cijian\gitrepo
type .gitattributes
echo --- authors
git log --format="%%an <%%ae>" origin/tokyo-5070ti-blocks -5
git log --format="%%an <%%ae>" origin/main -3
echo --- revert
type D:\Cijian\logs\revveg.log
dir /b D:\Cijian\logs\revveg.done
findstr /L /C:"[cj] DONE" D:\Cijian\logs\shop_sf08_tent.log
