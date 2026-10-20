@echo off
setlocal
cd /d "%~dp0"
if not exist "install_instance.py" (echo Missing installer & exit /b 2)
if "%SST_WORKBENCH_ROOT%"=="" set "SST_WORKBENCH_ROOT=C:\workspace\projects\SST-Workbench"
set "DST=%SST_WORKBENCH_ROOT%\01_research\F_exploratory\GPE_EXT_001_GPE_GPU_Benchmark_v0.1.0"
if not exist "%DST%\GPE_INSTALL_MANIFEST.json" (
  py -3 install_instance.py --workbench "%SST_WORKBENCH_ROOT%" || exit /b %errorlevel%
)
call "%DST%\run_all.cmd" %*
exit /b %errorlevel%
