@echo off
setlocal
cd /d "%~dp0"
echo CPU/OpenMP spectral fallback; selection lock remains unchanged.
".venv\Scripts\python.exe" dispatch_target.py --prefer v048 spectral-v048 --mode selected --backend openmp
exit /b %ERRORLEVEL%
