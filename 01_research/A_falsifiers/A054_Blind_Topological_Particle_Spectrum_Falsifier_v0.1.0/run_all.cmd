@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set PRESET=%~1
if "%PRESET%"=="" set PRESET=basic
if /I not "%PRESET%"=="basic" if /I not "%PRESET%"=="full" (
  echo Usage: run_all.cmd [basic^|full]
  exit /b 2
)
echo [1/7] install
call run_00_install.cmd || exit /b 1
echo [2/7] C++17 / pybind11 / OpenMP build
call run_05_build_cpp.cmd || exit /b 1
echo [3/7] native-Python parity and topology selftest
call run_10_selftest.cmd || exit /b 1
echo [4/7] BLIND atlas campaign
call run_20_blind.cmd %PRESET% || exit /b 1
echo [5/7] recursive SHA-256 blind seal
call run_30_seal.cmd %PRESET% || exit /b 1
echo [6/7] reveal historical and SM reference layers
call run_40_reveal.cmd %PRESET% || exit /b 1
echo [7/7] package BLIND / REVEALED / combined archives
call run_50_package.cmd %PRESET% || exit /b 1
echo.
echo A054 v0.1.0 complete.
exit /b 0
