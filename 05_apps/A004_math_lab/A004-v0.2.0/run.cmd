@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo SST Math Lab v0.2.0
echo ============================================================

if not exist "lib\math.js" call install_libs.cmd
if errorlevel 1 exit /b 1
if not exist "lib\numeric-1.2.6.min.js" call install_libs.cmd
if errorlevel 1 exit /b 1
if not exist "lib\numeral.min.js" call install_libs.cmd
if errorlevel 1 exit /b 1
if not exist "lib\bignumber.min.js" call install_libs.cmd
if errorlevel 1 exit /b 1
if not exist "lib\accounting.min.js" call install_libs.cmd
if errorlevel 1 exit /b 1
if not exist "lib\plotly.min.js" call install_libs.cmd
if errorlevel 1 exit /b 1

echo Opening SST Math Lab...
start "" "%~dp0index.html"
exit /b 0
