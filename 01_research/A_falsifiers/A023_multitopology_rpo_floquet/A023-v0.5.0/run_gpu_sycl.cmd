@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_sycl_worker_smoke.cmd
exit /b %errorlevel%
