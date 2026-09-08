@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo [SST] v0.4.8 diagnostics use the external SYCL worker architecture.
call run_sycl_worker_smoke.cmd
exit /b %errorlevel%
