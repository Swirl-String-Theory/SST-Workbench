@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not defined SST_V048_DIR set "SST_V048_DIR=C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A023_multitopology_rpo_floquet\A023-v0.4.8"
if not defined SST_ATLAS_ROOT set "SST_ATLAS_ROOT=C:\workspace\projects\SST-Workbench\01_research\D_benchmarks\D009_knotplot_parameter_atlas\D009-v0.3.0"
call run_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
"%SST_V048_DIR%\.venv\Scripts\python.exe" tests\test_core.py
if errorlevel 1 exit /b %ERRORLEVEL%
"%SST_V048_DIR%\.venv\Scripts\python.exe" tests\test_static.py
exit /b %ERRORLEVEL%
