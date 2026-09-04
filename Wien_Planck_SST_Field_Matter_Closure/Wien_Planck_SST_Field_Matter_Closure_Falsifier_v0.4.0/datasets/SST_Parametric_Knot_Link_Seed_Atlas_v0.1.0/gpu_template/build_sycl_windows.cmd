@echo off
setlocal
cd /d "%~dp0"
icx /nologo /std:c++17 /EHsc /O2 /fsycl sycl_biot_screen.cpp /Fe:sycl_biot_screen.exe
if errorlevel 1 exit /b 1
sycl_biot_screen.exe
