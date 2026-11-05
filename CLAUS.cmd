@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Execute SETUP.ps1 antes de abrir o Claus.
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "desktop.py"
