@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe call run_install.cmd || exit /b 1
set "ONEAPI_DEVICE_SELECTOR=level_zero:gpu"
set "SYCL_CACHE_PERSISTENT=0"
.venv\Scripts\python.exe tools\build_sycl_worker.py || exit /b 1
.venv\Scripts\python.exe tools\sycl_worker_smoke.py || exit /b 1
