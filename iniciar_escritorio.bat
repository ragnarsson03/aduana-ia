@echo off
setlocal
cd /d "%~dp0"
echo ========================================================
echo   Aduana IA — Perimetro Soberano (Escritorio Nativo)
echo ========================================================
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m app.desktop
) else (
    python -m app.desktop
)
endlocal
