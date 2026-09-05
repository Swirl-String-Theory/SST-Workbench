@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Hopf FULL + HIGHRES C++ validation v0.1.3
echo WARNING: HIGHRES/director convergence may require several GB RAM.
echo ============================================================

echo [1/4] Full quick+standard native validation
call "RUN_FULL_VALIDATION.cmd"
if errorlevel 1 goto :fail

echo [2/4] Full HIGHRES H0-H10 C++ chain
call "cmd\04_RUN_HIGHRES_CPP.cmd"
if errorlevel 1 goto :fail

echo [3/4] Focused HIGHRES Hopf H0-H3/Hodge run
call "cmd\10_RUN_HIGHRES_HOPF.cmd"
if errorlevel 1 goto :fail

echo [4/4] Director/Hodge convergence ladder
call "cmd\09_RUN_DIRECTOR_CONVERGENCE.cmd"
if errorlevel 1 goto :fail

echo ============================================================
echo PASS - full v0.1.3 high-resolution validation complete.
echo Results:
echo   results\high_cpp\run_summary.json
echo   results\highres_hopf\step04\H1_H3_evidence.json
echo   results\director_convergence\director_convergence.json
echo ============================================================
exit /b 0

:fail
echo ============================================================
echo FAIL - high-resolution validation stopped.
echo Inspect the latest results and logs.
echo ============================================================
exit /b 1
