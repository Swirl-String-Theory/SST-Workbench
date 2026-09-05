@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
echo ============================================================
echo 3_MAXWELL v0.2.0 - EXTENDED blind campaign
echo All *_final.txt geometries + anchor convergence/core sweeps
echo Knots: %KNOTS_DIR%
echo Threads: %SST_NATIVE_THREADS%
echo C++ native backend REQUIRED
echo ============================================================
"%PY%" -m sst_maxwell3_blind.cli run --profile extended --knots "%KNOTS_DIR%" --threads %SST_NATIVE_THREADS% --force-build
set RC=%errorlevel%
echo.
if %RC%==0 (echo [3_MAXWELL] EXTENDED completed without FAIL.) else (echo [3_MAXWELL] EXTENDED returned code %RC%.)
exit /b %RC%
