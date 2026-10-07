@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
rem v1.0.3 tests Python FP64, C++ FP64, SYCL FP32 and SYCL DD32/FP32x2 on identical kernels.
set "SST_SYCL_ALLOW_FP32=1"
%PY% tools\backend_selftest.py --allow-sycl-fp32 --force-build
exit /b %ERRORLEVEL%
