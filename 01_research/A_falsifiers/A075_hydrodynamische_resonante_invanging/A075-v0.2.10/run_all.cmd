@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" goto help
if /I "%~1"=="VERIFY" goto run
if /I "%~1"=="PILOT" goto run
if /I "%~1"=="SCAN" goto run
if /I "%~1"=="SELFTEST" goto test
echo Unsupported command - no action performed
exit /b 2
:run
python -m ruban_equilibrium.runner %*
exit /b %errorlevel%
:test
python -m pytest -q tests
exit /b %errorlevel%
:help
echo A075-v0.2.10 Ruban equilibrium addon - standalone, no Framework promotion
echo run_all.cmd SELFTEST
 echo run_all.cmd VERIFY
 echo run_all.cmd PILOT --n 128 --harmonics 1 --modes 4
 echo run_all.cmd SCAN --n 256 --harmonics 2 --modes 6
exit /b 0
