@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="SELFTEST" goto test
if /I "%~1"=="VERIFY" goto run
if /I "%~1"=="EQUILIBRIUM" goto run
if /I "%~1"=="SPECTRUM" goto run
if /I "%~1"=="QUALIFY" goto run
echo A075-v0.2.11 standalone Ruban equilibrium / discrete spectrum
 echo run_all.cmd SELFTEST
 echo run_all.cmd VERIFY
 echo run_all.cmd EQUILIBRIUM --n-levels 64,128 --harmonics 3
 echo run_all.cmd SPECTRUM --n-levels 48,64 --harmonics 2
 echo run_all.cmd QUALIFY --n-levels 48,64 --harmonics 2
exit /b 2
:run
python -m ruban_equilibrium.qualification %*
exit /b %errorlevel%
:test
python -m pytest -q tests
exit /b %errorlevel%
