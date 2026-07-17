@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem run_three_stage.cmd — recommended KnotPlot-seed tightening pipeline
rem
rem Usage:
rem   run_three_stage.cmd path\to\selected_trial.txt
rem
rem Typical seed comes from select_knotplot_seed.py (not blindly 015k).
rem
rem Stage 1: -a --EqOn          coarse tighten (residual 0.05, max 10k)
rem Stage 2: -c --EqForceOn     equilateralize + converge (residual 0.01, max 50k)
rem Stage 3: -c --EqOn          unbiased polish (residual 0.01, max 20k)
rem
rem Polish output (*_rr_020k_polish.txt) is the near-ideal candidate.

set "BUNDLE=%~dp0"
set "RR=%BUNDLE%ridgerunner.cmd"

if "%~1"=="" (
  echo Usage: run_three_stage.cmd path\to\seed.txt
  exit /b 1
)
if /I "%~1"=="-h" goto :usage
if /I "%~1"=="--help" goto :usage
if /I "%~1"=="/?" goto :usage

if not exist "%RR%" (
  echo ERROR: ridgerunner.cmd not found: "%RR%"
  exit /b 1
)

set "SEED=%~f1"
if not exist "%SEED%" (
  echo ERROR: seed not found: "%SEED%"
  exit /b 1
)

for %%F in ("%SEED%") do (
  set "SEED_DIR=%%~dpF"
  set "SEED_STEM=%%~nF"
)

set "R1=%SEED_DIR%%SEED_STEM%_rr_010k_coarse.txt"
set "R2=%SEED_DIR%%SEED_STEM%_rr_010k_coarse_rr_050k_eqfinal.txt"
set "R3=%SEED_DIR%%SEED_STEM%_rr_010k_coarse_rr_050k_eqfinal_rr_020k_polish.txt"

echo.
echo ============================================================
echo Three-stage ridgerunner
echo Seed: %SEED%
echo ============================================================

echo.
echo [1/3] coarse: -a --EqOn -s 10000 --StopResidual=0.05
echo Expect: %R1%
call "%RR%" -a --EqOn -s 10000 --StopResidual=0.05 --label coarse "%SEED%"
if errorlevel 1 (
  echo ERROR: stage 1 ^(coarse^) failed
  exit /b 1
)
if not exist "%R1%" (
  echo ERROR: stage 1 output missing: "%R1%"
  exit /b 1
)

echo.
echo [2/3] eqfinal: -c --EqForceOn -s 50000 --StopResidual=0.01
echo Expect: %R2%
call "%RR%" -c --EqForceOn -s 50000 --StopResidual=0.01 --Stop20=0.000001 --label eqfinal "%R1%"
if errorlevel 1 (
  echo ERROR: stage 2 ^(eqfinal^) failed
  exit /b 1
)
if not exist "%R2%" (
  echo ERROR: stage 2 output missing: "%R2%"
  exit /b 1
)

echo.
echo [3/3] polish: -c --EqOn -s 20000 --StopResidual=0.01
echo Expect: %R3%
call "%RR%" -c --EqOn -s 20000 --StopResidual=0.01 --Stop20=0.0000001 --label polish "%R2%"
if errorlevel 1 (
  echo ERROR: stage 3 ^(polish^) failed
  exit /b 1
)
if not exist "%R3%" (
  echo ERROR: stage 3 output missing: "%R3%"
  exit /b 1
)

echo.
echo Done. Near-ideal candidate:
echo   %R3%
exit /b 0

:usage
echo.
echo Usage: run_three_stage.cmd path\to\seed.txt
echo.
echo Stage 1: ridgerunner -a --EqOn -s 10000 --StopResidual=0.05 --label coarse
echo Stage 2: ridgerunner -c --EqForceOn -s 50000 --StopResidual=0.01 --Stop20=0.000001 --label eqfinal
echo Stage 3: ridgerunner -c --EqOn -s 20000 --StopResidual=0.01 --Stop20=0.0000001 --label polish
echo.
exit /b 1
