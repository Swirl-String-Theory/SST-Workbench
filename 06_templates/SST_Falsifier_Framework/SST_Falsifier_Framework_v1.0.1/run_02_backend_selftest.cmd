@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
rem Arc-class devices commonly expose FP32 for this worker; this enables screening explicitly.
set "SST_SYCL_ALLOW_FP32=1"
%PY% tools\backend_selftest.py --allow-sycl-fp32 --force-build
exit /b %ERRORLEVEL%
