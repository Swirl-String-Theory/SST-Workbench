@echo off
setlocal
cd /d "%~dp0.."
python -m pytest -q tests
if errorlevel 1 exit /b 1
if not exist build mkdir build
where g++ >nul 2>&1
if not errorlevel 1 (
  g++ -O2 -std=c++17 native\ring_cli.cpp -o build\ring_cli.exe
)
python -m science.run_science --cpp --archive
exit /b %errorlevel%
