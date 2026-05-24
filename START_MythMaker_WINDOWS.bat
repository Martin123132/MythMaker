@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo MythMaker needs Python 3.10 or newer.
  echo.
  echo Install Python from https://www.python.org/downloads/windows/
  echo Make sure you tick "Add python.exe to PATH" during install.
  echo Then double-click this file again.
  echo.
  pause
  exit /b 1
)
python -m mythmaker_app.app
pause
