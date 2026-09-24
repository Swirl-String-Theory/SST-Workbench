@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo  E010 PKLSA FREMLIN 8_5 RESTORE + FINAL REPAIR
echo ============================================================
echo.

call install_8_5_short.cmd "%~1"
if errorlevel 1 goto :fail

echo.
call run_repair_final_a007_header_only.cmd "%~1"
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo [OK] 8_5 source restore and targeted production repair complete.
echo ============================================================
exit /b 0

:fail
echo.
echo ============================================================
echo [FAIL] 8_5 restore/repair stopped fail-closed.
echo ============================================================
exit /b 1
