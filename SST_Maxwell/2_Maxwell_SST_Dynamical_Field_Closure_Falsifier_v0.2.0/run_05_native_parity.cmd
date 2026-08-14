@echo off
setlocal EnableExtensions
call "%~dp0_paths.cmd"
cd /d "%ROOT%"
if not exist "%PY%" (echo [ERROR] Run run_00_install.cmd first.& exit /b 1)
"%PY%" run_native_parity.py --knots-dir "%SST_KNOTS_DIR%" --file knot_3.1_final.txt --threads %SST_NATIVE_THREADS% --require-native
exit /b %ERRORLEVEL%
