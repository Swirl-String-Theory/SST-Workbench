@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo SST Threaded-Hole Substrate Blind Falsifier v0.2.1 - INSTALL
echo ============================================================
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -e .
if errorlevel 1 exit /b 1
echo [SST-TH] Python environment ready.
exit /b 0
