@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Material-Coordinate / Phase-Shift EFT Falsifier v0.1.0
echo Environment setup
echo ============================================================
if not exist .venv (
  py -3 -m venv .venv 2>nul
  if errorlevel 1 python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
python -m native_ext.build_ext_if_needed
if errorlevel 1 echo [WARN] Native build failed. BASIC uses Python fallback; EXTENDED requires native.
python -m pytest tests -q
if errorlevel 1 exit /b 1
echo [OK] setup complete
endlocal
