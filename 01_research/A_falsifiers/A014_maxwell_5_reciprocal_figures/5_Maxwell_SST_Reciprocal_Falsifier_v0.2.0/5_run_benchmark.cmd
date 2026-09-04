@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call 5_env.cmd
if errorlevel 1 exit /b %errorlevel%
set "THREADS=%NUMBER_OF_PROCESSORS%"
if "%THREADS%"=="" set "THREADS=8"
if not "%~1"=="" set "THREADS=%~1"
set "KNOTS=%M5_KNOTS_DEFAULT%"
if not "%~2"=="" set "KNOTS=%~2"
"%M5_PY%" tools\5_benchmark_native.py --knots-dir "%KNOTS%" --threads %THREADS%
exit /b %errorlevel%
