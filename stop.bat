@echo off
cd /d "%~dp0"
echo Eski bot jarayonlari to'xtatilmoqda...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop.ps1"
ping 127.0.0.1 -n 2 >nul
