@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo SST cpp_pybind audit template - FULL RUN
echo ============================================================

call "%~dp0run_install.cmd"
if errorlevel 1 goto :fail

set "PY=.venv\Scripts\python.exe"

echo [build] Native C++ extension (fallback remains usable)...
"%PY%" -m native_ext.build_ext_if_needed --force
if errorlevel 1 (
  echo [WARN] Native build failed; continuing with Python fallback.
)

echo [checks] Full falsifier battery...
"%PY%" run_all_checks.py --force-build %*
if errorlevel 1 goto :fail

echo ============================================================
echo COMPLETE - results under {folder}_outputs\
echo ============================================================
exit /b 0

:fail
echo ============================================================
echo FAILED - inspect messages above.
echo ============================================================
exit /b 1
