@echo off
setlocal
cd /d "%~dp0"
python run_performance_benchmark.py --n 48 --shell 2 --threads 16 %*
exit /b %ERRORLEVEL%
