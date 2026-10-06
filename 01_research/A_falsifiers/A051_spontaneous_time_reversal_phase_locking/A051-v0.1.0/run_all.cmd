@echo off
setlocal
cd /d "%~dp0"
call run_python.cmd
if errorlevel 1 exit /b %errorlevel%
echo.
echo [A051] Python reference qualification complete.
echo [A051] Native parity is optional: run_build_cpp.cmd then run_native_parity.cmd
endlocal
