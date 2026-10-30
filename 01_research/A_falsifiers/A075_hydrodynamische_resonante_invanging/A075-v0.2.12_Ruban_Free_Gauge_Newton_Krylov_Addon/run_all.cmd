@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="SELFTEST" goto test
if /I "%~1"=="VERIFY" goto run
if /I "%~1"=="GAUGE_NEWTON" goto run
if /I "%~1"=="CONTINUE" goto run
echo A075-v0.2.12 Research addon - no Framework gates promoted
echo run_all.cmd SELFTEST
echo run_all.cmd VERIFY
echo run_all.cmd GAUGE_NEWTON --n-levels 64,128 --run-id LOCAL_GAUGE_001
echo run_all.cmd CONTINUE --n-levels 128,256,512,1024 --allow-expensive --run-id LOCAL_CONTINUATION_001
exit /b 2
:run
python -m ruban_equilibrium.gauge_runner %*
exit /b %errorlevel%
:test
python -m pytest -q tests
exit /b %errorlevel%
