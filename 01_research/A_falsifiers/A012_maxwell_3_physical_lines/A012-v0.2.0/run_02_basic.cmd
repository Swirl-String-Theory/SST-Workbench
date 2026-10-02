@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
echo ============================================================
echo 3_MAXWELL v0.2.0 - BASIC blind campaign
echo Anchors: trefoil, figure-eight, T(2,3), 2-component link
echo Knots: %KNOTS_DIR%
echo Threads: %SST_NATIVE_THREADS%
echo ============================================================
"%PY%" -m sst_maxwell3_blind.cli run --profile basic --knots "%KNOTS_DIR%" --threads %SST_NATIVE_THREADS%
set RC=%errorlevel%
echo.
if %RC%==0 (echo [3_MAXWELL] BASIC completed without FAIL.) else (echo [3_MAXWELL] BASIC returned code %RC%.)
exit /b %RC%
