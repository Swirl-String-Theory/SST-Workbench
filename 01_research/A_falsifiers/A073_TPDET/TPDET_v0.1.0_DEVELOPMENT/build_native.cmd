@echo off
setlocal
cd /d "%~dp0"
if not exist native\bin mkdir native\bin
where g++ >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  g++ -std=c++17 -O3 -fopenmp -shared -o native\bin\bs_native.dll native\biot_savart.cpp
  exit /b %ERRORLEVEL%
)
where cl >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  cl /nologo /O2 /EHsc /openmp /LD native\biot_savart.cpp /link /OUT:native\bin\bs_native.dll
  exit /b %ERRORLEVEL%
)
echo Neither MinGW g++ nor MSVC cl available. Python fallback remains functional.
exit /b 2
