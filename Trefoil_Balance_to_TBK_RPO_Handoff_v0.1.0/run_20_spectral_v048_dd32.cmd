@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" dispatch_target.py --prefer v048 spectral-v048 --mode selected --backend sycl-dd32
exit /b %ERRORLEVEL%
