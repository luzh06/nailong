@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Cijian\scripts\bg.ps1 fetch "C:\Python314\python.exe -I D:\Cijian\scripts\ph_fetch.py"
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Cijian\scripts\bg.ps1 venv "C:\Python314\python.exe -m venv D:\Cijian\tools\pyenv && D:\Cijian\tools\pyenv\Scripts\python.exe -m pip install --no-input pillow numpy"
dir /b D:\Cijian\scripts
