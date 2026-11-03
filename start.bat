@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0dist\ChatAndChess.exe" (
    "%~dp0dist\ChatAndChess.exe" %*
    exit /b %ERRORLEVEL%
)
where py >nul 2>&1
if not errorlevel 1 (
    py -3 "%~dp0chess.py" %*
    set "exit_code=%ERRORLEVEL%"
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo Python 3 wurde nicht gefunden.
        pause
        exit /b 1
    )
    python "%~dp0chess.py" %*
    set "exit_code=%ERRORLEVEL%"
)
if not "%exit_code%"=="0" pause
exit /b %exit_code%
