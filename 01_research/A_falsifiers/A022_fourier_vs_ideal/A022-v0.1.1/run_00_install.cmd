@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Fourier-vs-Ideal Blind Falsifier v0.1.1 - INSTALL
echo ============================================================
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 exit /b 1
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
python -m pip install -e . -r requirements.txt
if errorlevel 1 exit /b 1
echo [SST-FVI] Python environment ready.
exit /b 0
