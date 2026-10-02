@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Voer eerst batch\01_setup_venv.bat uit.
  pause
  exit /b 1
)
set PY_CMD="%ROOT%\.venv\Scripts\python.exe"
echo === v0.3.0 AXIAL BUNDLE SELFTEST ===
%PY_CMD% src\sst_axial_vortex_bundle.py selftest
if errorlevel 1 goto :fail
echo [PASS] Axiale bundel-selftest geslaagd.
pause
exit /b 0
:fail
echo [FAIL] Axiale bundel-selftest faalde.
pause
exit /b 1
