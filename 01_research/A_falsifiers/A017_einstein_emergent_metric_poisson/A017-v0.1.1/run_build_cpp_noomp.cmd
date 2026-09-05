@echo off
setlocal
cd /d "%~dp0"
set "SST_DISABLE_OPENMP=1"
echo ============================================================
echo [SST] Diagnostic native build WITHOUT OpenMP
 echo ============================================================
call run_build_cpp.cmd
exit /b %errorlevel%
