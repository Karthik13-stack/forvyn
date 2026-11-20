@echo off
REM Run LexiLaw Backend + Frontend
cd /d "%~dp0backend"
echo Starting LexiLaw Backend...
echo.
echo Server will be available at: http://127.0.0.1:8000
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
