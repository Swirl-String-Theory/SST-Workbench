@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if not errorlevel 1 (
  python "%~dp0setup_A068.py" %*
) else (
  py -3 "%~dp0setup_A068.py" %*
)
if errorlevel 1 (
  echo.
  echo SETUP FAILED. Read the error above. Existing frozen instances were not overwritten.
  pause
  exit /b 1
)
echo.
echo SETUP COMPLETE. Check the messages above for the official FREEZE status.
pause
exit /b 0
