@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
echo ============================================================
echo 3_MAXWELL v0.2.0 - BASIC pure-Python reference run
echo Slow by design; useful as an implementation cross-check.
echo ============================================================
"%PY%" -m sst_maxwell3_blind.cli run --profile basic --knots "%KNOTS_DIR%" --threads 1 --force-python
exit /b %errorlevel%
