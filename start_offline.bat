@echo off
title AgriStock Pro - 100%% Offline Local Launcher
echo ============================================================
echo           AgriStock Pro - Starting Offline Mode             
echo ============================================================
echo.

cd /d "%~dp0backend"
echo [1/2] Starting Python FastAPI Backend Server (Port 8000)...
start "AgriStock Backend" cmd /k ".\venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000"

timeout /t 3 >nul

cd /d "%~dp0frontend"
echo [2/2] Starting React Frontend Server (Port 3000)...
start "AgriStock Frontend" cmd /k "npm start"

echo.
echo ============================================================
echo   AgriStock Pro is running offline!                         
echo   Open your browser at: http://localhost:3000               
echo ============================================================
echo.
pause
