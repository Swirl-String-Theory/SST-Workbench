@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
echo ============================================================
echo 3_MAXWELL v0.2.0 - C++ vs Python benchmark
echo ============================================================
"%PY%" -m sst_maxwell3_blind.cli benchmark --profile basic --knots "%KNOTS_DIR%" --threads %SST_NATIVE_THREADS%
exit /b %errorlevel%
