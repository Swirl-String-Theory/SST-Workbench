@echo off
setlocal
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=SMOKE"
if /I "%MODE%"=="TEST" (
  py -m pytest -q tests
  if errorlevel 1 exit /b 1
  exit /b 0
)
py -m pytest -q tests
if errorlevel 1 exit /b 1
if /I "%MODE%"=="CONVERGE" (
  py -m ruban_falsifier.convergence
  if errorlevel 1 exit /b 1
  exit /b 0
)
py -m ruban_falsifier "%MODE%"
if errorlevel 1 exit /b 1
exit /b 0
