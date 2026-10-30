@echo off
setlocal
cd /d "%~dp0"
call _sst_runtime\run_sycl_dd32_smoke.cmd
exit /b %ERRORLEVEL%
