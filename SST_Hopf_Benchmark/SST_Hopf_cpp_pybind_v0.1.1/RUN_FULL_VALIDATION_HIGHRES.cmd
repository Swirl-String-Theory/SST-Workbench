@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Hopf FULL + HIGHRES C++ validation
echo WARNING: HIGHRES may require several GB RAM.
echo ============================================================
call "RUN_FULL_VALIDATION.cmd"
if errorlevel 1 goto :fail

echo [HIGHRES] H0-H10 C++ chain
call "cmd\04_RUN_HIGHRES_CPP.cmd"
if errorlevel 1 goto :fail

echo ============================================================
echo PASS - full validation including HIGHRES complete.
echo See results\high_cpp\run_summary.json
echo ============================================================
exit /b 0

:fail
echo ============================================================
echo FAIL - high-resolution validation stopped.
echo ============================================================
exit /b 1
