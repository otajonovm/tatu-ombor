@echo off
cd /d "%~dp0"
echo TATU bot va TMA API alohida oynalarda ishga tushmoqda...
start "TATU TMA API" cmd /k "cd /d %~dp0 && .\.venv\Scripts\python.exe -m uvicorn web_api:app --host 0.0.0.0 --port 8000"
start "TATU Telegram Bot" cmd /k "cd /d %~dp0 && .\.venv\Scripts\python.exe main.py"
echo Tayyor. Ikkala oyna ochiq qoldiriladi.
