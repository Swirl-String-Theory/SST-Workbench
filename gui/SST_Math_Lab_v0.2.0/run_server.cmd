@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set PORT=8787

echo ============================================================
echo SST Math Lab v0.2.0 - local HTTP server
echo ============================================================

if not exist "lib\math.js" call install_libs.cmd
if errorlevel 1 exit /b 1
if not exist "lib\numeric-1.2.6.min.js" call install_libs.cmd
if errorlevel 1 exit /b 1
if not exist "lib\plotly.min.js" call install_libs.cmd
if errorlevel 1 exit /b 1

where py >nul 2>nul
if %errorlevel%==0 (
  start "SST Math Lab Server" cmd /k "cd /d ""%~dp0"" && py -3 -m http.server %PORT% --bind 127.0.0.1"
  timeout /t 1 /nobreak >nul
  start "" "http://127.0.0.1:%PORT%/"
  exit /b 0
)
where python >nul 2>nul
if %errorlevel%==0 (
  start "SST Math Lab Server" cmd /k "cd /d ""%~dp0"" && python -m http.server %PORT% --bind 127.0.0.1"
  timeout /t 1 /nobreak >nul
  start "" "http://127.0.0.1:%PORT%/"
  exit /b 0
)
echo ERROR: Python not found. Use run.cmd instead.
pause
exit /b 1
