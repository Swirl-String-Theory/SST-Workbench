@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
set PY_CMD="%ROOT%\.venv\Scripts\python.exe"

%PY_CMD% src\sst_iso_gamma_area_clock.py selftest
if errorlevel 1 goto :fail

echo.
echo [OK] De onafhankelijke fase- en periode-extractors zijn geslaagd.
pause
exit /b 0
:fail
echo [ERROR] C9 selftest faalde.
pause
exit /b 1
