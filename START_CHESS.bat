@echo off
chcp 65001 >nul
echo.
echo   [1] Schach starten
echo   [2] Worker starten (fuer Claude Code Modus)
echo.
set /p choice="  Auswahl: "
if "%choice%"=="2" (
    python "%~dp0chess.py" --worker
) else (
    python "%~dp0chess.py"
)
pause
