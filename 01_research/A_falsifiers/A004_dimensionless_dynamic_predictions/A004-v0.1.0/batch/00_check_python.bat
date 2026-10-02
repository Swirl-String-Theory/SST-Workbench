@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
echo.
echo [OK] Pakketmap: %ROOT%
echo [OK] Python-opdracht: %PY_CMD%
%PY_CMD% --version
%PY_CMD% -c "import sys, platform; print('Executable:', sys.executable); print('Platform:', platform.platform())"
echo.
pause
