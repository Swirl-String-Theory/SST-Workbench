@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1

where icx >nul 2>nul
if errorlevel 1 if exist "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" >nul
if errorlevel 1 if exist "C:\Program Files\Intel\oneAPI\setvars.bat" call "C:\Program Files\Intel\oneAPI\setvars.bat" >nul

where icx >nul 2>nul
if errorlevel 1 (
  echo ERROR: Intel oneAPI icx not found.
  echo Install Intel oneAPI Base/HPC Toolkit or use run_all_cpu_fallback.cmd.
  popd
  exit /b 2
)

echo [GPU] Building FP32 SYCL broad-screen backend...
icx -std=c++17 -O3 -fsycl sycl_funnel.cpp -DSST_GPU_FP32=1 -o sycl_funnel_fp32.exe
if errorlevel 1 (
  echo [GPU] First icx syntax failed; trying Windows-style driver flags...
  icx /std:c++17 /O2 /fsycl sycl_funnel.cpp /DSST_GPU_FP32=1 /Fe:sycl_funnel_fp32.exe
)
if errorlevel 1 exit /b 1

echo [GPU] Optional FP64 build...
icx -std=c++17 -O3 -fsycl sycl_funnel.cpp -DSST_GPU_FP64=1 -o sycl_funnel_fp64.exe >nul 2>nul
if errorlevel 1 echo [GPU] FP64 executable not built. This is non-fatal; screening uses FP32 and CPU-double certification follows.

echo [GPU] FP32 executable ready: %CD%\sycl_funnel_fp32.exe
popd
endlocal
