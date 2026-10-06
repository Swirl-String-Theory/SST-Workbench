@echo off
setlocal
cd /d "%~dp0"
where cl >nul 2>nul
if errorlevel 1 (
  echo [A051] MSVC cl.exe not found. Run from a Visual Studio Developer Command Prompt.
  exit /b 2
)
if not exist build mkdir build
cl /nologo /std:c++17 /EHsc /O2 cpp\trpl_reference_cli.cpp /Fe:build\trpl_reference_cli.exe
if errorlevel 1 exit /b %errorlevel%
build\trpl_reference_cli.exe 1.3 0.1 1.0 0.005 2000
endlocal
