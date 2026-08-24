@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Finite-Core Phase Falsifier v0.1.1 - INSTALL
echo ============================================================
if not exist .venv py -3 -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -e . --no-build-isolation
if errorlevel 1 exit /b 1
echo [FC-PHASE] Python environment ready.
