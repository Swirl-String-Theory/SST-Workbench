@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not defined SST_V048_DIR set "SST_V048_DIR=C:\workspace\projects\SST-Workbench\SST_Trefoil_Lobe_Orientation_Blind_Falsifier\SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact"
if not defined SST_ATLAS_ROOT set "SST_ATLAS_ROOT=C:\workspace\projects\SST-Workbench\KnotPlot\KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_v0.3.0"
if not exist "%SST_V048_DIR%\VERSION.json" (
  echo ERROR: target v0.4.8 not found: %SST_V048_DIR%
  exit /b 2
)
if not exist "%SST_V048_DIR%\.venv\Scripts\python.exe" (
  echo [RPO] target venv missing - running v0.4.8 installer...
  call "%SST_V048_DIR%\run_install.cmd"
  if errorlevel 1 exit /b %ERRORLEVEL%
)
call run_preflight.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_extended.cmd
exit /b %ERRORLEVEL%
