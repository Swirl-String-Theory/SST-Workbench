@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
set "SST_SYCL_ALLOW_FP32=1"
%PY% tools\backend_selftest.py --allow-sycl-fp32 --skip-cpp --force-build --json build\DD32_PARITY_SMOKE.json
exit /b %ERRORLEVEL%
