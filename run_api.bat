@echo off
cd /d "%~dp0"
echo TATU TMA API ishga tushmoqda...
.\.venv\Scripts\python.exe -m uvicorn web_api:app --host 0.0.0.0 --port 8000
pause
