@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
call gpu\build_sycl_windows.cmd || exit /b 1
if not exist gpu\sycl_funnel_fp32.exe (echo ERROR: GPU executable missing after build. & popd & exit /b 2)
popd
endlocal
