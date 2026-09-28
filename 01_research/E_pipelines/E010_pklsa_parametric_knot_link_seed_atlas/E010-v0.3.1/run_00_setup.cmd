@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist .venv (
  py -3 -m venv .venv
  if errorlevel 1 exit /b 1
)

call .venv\Scripts\activate.bat
if errorlevel 1 exit /b 1

python -m pip install --upgrade pip setuptools wheel pybind11
if errorlevel 1 exit /b 1

python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

rem Install the Python packages first, but deliberately defer the C++ extension.
rem run_all.cmd performs the native build as a separate, explicit MSVC gate.
set "PKLSA_NO_NATIVE=1"
python -m pip install -e .
set "PIP_RC=%ERRORLEVEL%"
set "PKLSA_NO_NATIVE="
if not "%PIP_RC%"=="0" exit /b %PIP_RC%

endlocal
exit /b 0
