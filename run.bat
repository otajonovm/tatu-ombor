@echo off
cd /d "%~dp0"
call stop.bat
echo.
echo ============================================
echo   TATU Ombor boti ishga tushmoqda...
echo   FAQAT shu oynani ochiq qoldiring!
echo ============================================
.\.venv\Scripts\python.exe main.py
pause
