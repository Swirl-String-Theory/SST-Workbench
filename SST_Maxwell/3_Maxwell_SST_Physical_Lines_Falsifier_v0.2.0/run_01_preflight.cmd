@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
echo ============================================================
echo 3_MAXWELL v0.2.0 - preflight
echo Knots: %KNOTS_DIR%
echo Threads: %SST_NATIVE_THREADS%
echo ============================================================
"%PY%" -m sst_maxwell3_blind.cli preflight --profile basic --knots "%KNOTS_DIR%" --threads %SST_NATIVE_THREADS% --force-build
exit /b %errorlevel%
