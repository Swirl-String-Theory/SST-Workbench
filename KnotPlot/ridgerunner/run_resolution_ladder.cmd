@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem run_resolution_ladder.cmd — resolution convergence from N=300 RR polish
rem
rem   run_resolution_ladder.cmd path\to\*_polish.txt
rem
rem Independently (same N=300 polish as source for both):
rem   resample --points 600  → coarse/eqfinal/polish (StopResidual 0.005)
rem   resample --points 1200 → same
rem
rem Output naming follows ridgerunner.cmd:
rem   {uniform}_rr_{stepsTag}_{label}.txt

set "BUNDLE=%~dp0"
set "RR=%BUNDLE%ridgerunner.cmd"
set "ROOT=%BUNDLE%.."
set "RESAMPLE=%ROOT%\resample_closed_knot_txt.py"

if "%~1"=="" (
  echo Usage: run_resolution_ladder.cmd path\to\N300_polish.txt
  exit /b 1
)
if /I "%~1"=="-h" goto :usage
if /I "%~1"=="--help" goto :usage
if /I "%~1"=="/?" goto :usage

if not exist "%RR%" (
  echo ERROR: missing "%RR%"
  exit /b 1
)
if not exist "%RESAMPLE%" (
  echo ERROR: missing "%RESAMPLE%"
  exit /b 1
)

set "POLISH=%~f1"
if not exist "%POLISH%" (
  echo ERROR: polish not found: "%POLISH%"
  exit /b 1
)

for %%F in ("%POLISH%") do (
  set "PDIR=%%~dpF"
  set "PSTEM=%%~nF"
)

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: python not found on PATH
  exit /b 1
)

call :ladder 600 20000 020k
if errorlevel 1 exit /b 1
call :ladder 1200 40000 040k
if errorlevel 1 exit /b 1

echo.
echo Resolution ladder finished for:
echo   %POLISH%
exit /b 0

:ladder
set "N=%~1"
set "COARSE_STEPS=%~2"
set "COARSE_TAG=%~3"
set "U=%PDIR%%PSTEM%_uniform_N%N%.txt"

echo.
echo ============================================================
echo Resolution ladder N=%N%  ^(from N=300 polish^)
echo ============================================================

python "%RESAMPLE%" "%POLISH%" --points %N%
if errorlevel 1 (
  echo ERROR: resample to N=%N% failed
  exit /b 1
)
if not exist "%U%" (
  echo ERROR: missing uniform N=%N%: "%U%"
  exit /b 1
)

echo [N=%N% 1/3] coarse -a --EqOn -s %COARSE_STEPS% --StopResidual=0.05 --label N%N%_coarse
call "%RR%" -a --EqOn -s %COARSE_STEPS% --StopResidual=0.05 --label N%N%_coarse "%U%"
if errorlevel 1 (
  echo ERROR: N=%N% coarse failed
  exit /b 1
)
set "C1=%PDIR%%PSTEM%_uniform_N%N%_rr_%COARSE_TAG%_N%N%_coarse.txt"
if not exist "%C1%" (
  echo ERROR: missing "%C1%"
  exit /b 1
)

echo [N=%N% 2/3] eqfinal -c --EqForceOn -s 50000 --StopResidual=0.005 --label N%N%_eqfinal
call "%RR%" -c --EqForceOn -s 50000 --StopResidual=0.005 --Stop20=0.000001 --label N%N%_eqfinal "%C1%"
if errorlevel 1 (
  echo ERROR: N=%N% eqfinal failed
  exit /b 1
)
set "C2=%PDIR%%PSTEM%_uniform_N%N%_rr_%COARSE_TAG%_N%N%_coarse_rr_050k_N%N%_eqfinal.txt"
if not exist "%C2%" (
  echo ERROR: missing "%C2%"
  exit /b 1
)

echo [N=%N% 3/3] polish -c --EqOn -s 30000 --StopResidual=0.005 --label N%N%_polish
call "%RR%" -c --EqOn -s 30000 --StopResidual=0.005 --Stop20=0.0000001 --label N%N%_polish "%C2%"
if errorlevel 1 (
  echo ERROR: N=%N% polish failed
  exit /b 1
)
set "C3=%PDIR%%PSTEM%_uniform_N%N%_rr_%COARSE_TAG%_N%N%_coarse_rr_050k_N%N%_eqfinal_rr_030k_N%N%_polish.txt"
if not exist "%C3%" (
  echo ERROR: missing "%C3%"
  exit /b 1
)

echo N=%N% polish: %C3%
exit /b 0

:usage
echo.
echo Usage: run_resolution_ladder.cmd path\to\N300_polish.txt
echo.
echo Resamples the same N=300 polish to N=600 and N=1200 independently,
echo then runs coarse / eqfinal / polish with --StopResidual=0.005.
exit /b 1
