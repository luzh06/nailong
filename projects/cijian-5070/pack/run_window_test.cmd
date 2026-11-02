@echo off
rem Double-click on the laptop: windowed Edge benchmark on the real GPU. Keep the window in front until numbers appear.
set PY=D:\Cijian\tools\blender-5.2.3-windows-x64\5.2\python\bin\python.exe
start "" /b "%PY%" D:\Cijian\web\srv.py D:\Cijian\pack 8765
timeout /t 2 >nul
start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --user-data-dir=D:\Cijian\pack\web\profile_w --no-first-run --new-window "http://127.0.0.1:8765/web/game.html?bench=1&name=w1"
