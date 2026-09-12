@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not defined SST_V048_DIR set "SST_V048_DIR=C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A023_multitopology_rpo_floquet\A023-v0.4.8"
if not defined SST_ATLAS_ROOT set "SST_ATLAS_ROOT=C:\workspace\projects\SST-Workbench\01_research\D_benchmarks\D009_knotplot_parameter_atlas\D009-v0.3.0"
if not exist "%SST_V048_DIR%\VERSION.json" (
  echo ERROR: target v0.4.8 not found: %SST_V048_DIR%
  exit /b 2
)
if not exist "%SST_V048_DIR%\.venv\Scripts\python.exe" (
  echo [RPO] target venv missing - running v0.4.8 installer...
  call "%SST_V048_DIR%\run_install.cmd"
  if errorlevel 1 exit /b %ERRORLEVEL%
)
"%SST_V048_DIR%\.venv\Scripts\python.exe" rpo_falsifier.py --config configs\extended.json --out-dir outputs\extended --target "%SST_V048_DIR%" --atlas "%SST_ATLAS_ROOT%"
exit /b %ERRORLEVEL%
