@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py run.py
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    python run.py
  ) else (
    echo Python is not installed.
    echo Get it from https://www.python.org/downloads/ and tick
    echo "Add python.exe to PATH" during setup, then run this again.
  )
)
pause
