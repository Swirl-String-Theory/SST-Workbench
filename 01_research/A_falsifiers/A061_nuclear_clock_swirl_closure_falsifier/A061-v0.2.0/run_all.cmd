@echo off
setlocal
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=BASIC"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
if /I "%MODE%"=="SETUP" (
  %PY% -m venv .venv || exit /b 1
  .venv\Scripts\python.exe -m pip install -r requirements.txt || exit /b 1
  exit /b 0
)
if /I "%MODE%"=="FETCH" (
  %PY% scripts\fetch_data.py
  exit /b %ERRORLEVEL%
)
if /I "%MODE%"=="SELFTEST" (
  %PY% run_instance.py SELFTEST || exit /b 1
  %PY% -m pytest -q tests || exit /b 1
  exit /b 0
)
if /I "%MODE%"=="BUILD_NATIVE" (
  %PY% -c "from framework_bootstrap import load_framework;load_framework();from sst_falsifier.native_build import build_pybind;from pathlib import Path;r=build_pybind(Path.cwd(),force=True);print(r.to_dict());raise SystemExit(0 if r.success else 1)"
  exit /b %ERRORLEVEL%
)
%PY% run_instance.py %MODE%
if errorlevel 1 exit /b %ERRORLEVEL%
if /I "%MODE%"=="CERTIFY" (
  %PY% scripts\assert_certified.py
  exit /b %ERRORLEVEL%
)
exit /b 0
