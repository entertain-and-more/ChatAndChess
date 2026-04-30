@echo off
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --name ChatAndChess ^
  --icon ChatAndChess.ico ^
  chess.py

if errorlevel 1 (
    echo.
    echo EXE build failed.
    pause
    exit /b 1
)

echo.
echo Build finished: dist\ChatAndChess.exe
pause
