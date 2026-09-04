@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not defined SST_V048_DIR set "SST_V048_DIR=C:\workspace\projects\SST-Workbench\SST_Trefoil_Lobe_Orientation_Blind_Falsifier\SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact"
if not defined SST_ATLAS_ROOT set "SST_ATLAS_ROOT=C:\workspace\projects\SST-Workbench\KnotPlot\KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_v0.3.0"
call run_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
"%SST_V048_DIR%\.venv\Scripts\python.exe" tests\test_core.py
if errorlevel 1 exit /b %ERRORLEVEL%
"%SST_V048_DIR%\.venv\Scripts\python.exe" tests\test_static.py
exit /b %ERRORLEVEL%
