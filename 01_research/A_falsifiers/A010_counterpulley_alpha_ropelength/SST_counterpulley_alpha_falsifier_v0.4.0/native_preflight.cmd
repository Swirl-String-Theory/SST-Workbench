@echo off
setlocal
python run_native_preflight.py --force-build --verbose
exit /b %errorlevel%
