@echo off
setlocal
cd /d "%~dp0\.."
call "cmd\_ENSURE_NATIVE.cmd"
if errorlevel 1 exit /b 1
set SST_HOPF_FORCE_PYTHON=0
set OUT=results\highres_hopf
if not exist "%OUT%" mkdir "%OUT%"
echo [SST-HOPF] High-resolution analytic Hopf benchmark...
.venv\Scripts\python.exe 02_analytische_hopf_benchmark.py --output "%OUT%\step02" --resolutions 48 64 96 128 --fiber-samples 1200 --integer-tolerance 0.05
if errorlevel 1 exit /b 1
echo [SST-HOPF] High-resolution director/Hodge certification...
.venv\Scripts\python.exe 04_hopf_lading_numeriek.py "%OUT%\step02\analytic_hopf_benchmark.npz" --output "%OUT%\step04" --director-order 4
exit /b %errorlevel%
