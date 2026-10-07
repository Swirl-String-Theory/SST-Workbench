@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo SST GPU SYCL/DPC++ audit template - FULL RUN (Arc worker)
echo ============================================================

call "%~dp0run_install.cmd"
if errorlevel 1 goto :fail

call "%~dp0run_arc.cmd" %*
if errorlevel 1 goto :fail

echo ============================================================
echo COMPLETE - see {folder}_outputs\
echo ============================================================
exit /b 0

:fail
echo ============================================================
echo FAILED - inspect messages above.
echo ============================================================
exit /b 1
