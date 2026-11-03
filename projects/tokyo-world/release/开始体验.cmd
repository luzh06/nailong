@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 此间 · 三日归途（体验期间请勿关闭）
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0serve.ps1"
if errorlevel 1 pause
