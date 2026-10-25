@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
if /I "%~1"=="STATIC" (
  call run_all_E010_v031.cmd %2 %3 %4
  exit /b !errorlevel!
)
if /I "%~1"=="SELFTEST" (
  call run_dynamics_v032.cmd SELFTEST
  exit /b !errorlevel!
)
if /I "%~1"=="BASIC" (
  call run_dynamics_v032.cmd BASIC
  if errorlevel 3 exit /b 3
  echo BASIC diagnostic completed. DYNAMICS_NOT_READY is a valid scientific result.
  exit /b 0
)
if /I "%~1"=="FULL" (
  call run_dynamics_v032.cmd FULL
  exit /b !errorlevel!
)
if /I "%~1"=="ALL" (
  call run_dynamics_v032.cmd SELFTEST
  if errorlevel 1 exit /b 1
  call run_dynamics_v032.cmd FULL
  exit /b !errorlevel!
)
echo Usage: run_all.cmd SELFTEST^|BASIC^|FULL^|ALL^|STATIC
exit /b 2
