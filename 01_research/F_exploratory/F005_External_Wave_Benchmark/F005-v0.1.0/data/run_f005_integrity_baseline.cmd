@echo off
setlocal
cd /d "%~dp0.."
py -3 data\f005_integrity_baseline_v0.3.0.py --root . %*
if errorlevel 1 (
 echo F005 v0.3.0 failed: check outputs or install numpy with py -3 -m pip install numpy
 exit /b 1
)
endlocal
