@echo off
set "PATH=%LOCALAPPDATA%\Programs\nodejs;%PATH%"
cd /d "%~dp0"
echo ========================================================
echo   Iniciando Aduana IA Frontend (React + Vite)
echo ========================================================
echo.
npm run dev
pause
