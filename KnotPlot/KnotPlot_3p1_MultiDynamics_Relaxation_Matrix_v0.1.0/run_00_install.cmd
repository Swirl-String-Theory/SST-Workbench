@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo SST Phase-Delay Knot Stability Falsifier v0.1.1 - INSTALL
echo ============================================================
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 exit /b 1
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

rem Critical v0.1.1 fix: initialize MSVC in this cmd process, then make
rem setuptools reuse it instead of spawning vcvarsall through nested cmd /c.
call "_ENSURE_MSVC.cmd"
if errorlevel 1 exit /b 1

python setup_native.py build_ext --inplace --force
if errorlevel 1 exit /b 1
set "PYTHONPATH=%CD%\src;%CD%"
python -m sst_phase_delay_falsifier.cli backend --require-cpp
if errorlevel 1 exit /b 1
python run_native_parity.py
if errorlevel 1 exit /b 1
python -m pytest -q
exit /b %ERRORLEVEL%
