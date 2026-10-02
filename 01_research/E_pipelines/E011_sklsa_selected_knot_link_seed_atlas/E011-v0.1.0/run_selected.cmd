@echo off
setlocal
cd /d "%~dp0"
rem E011-v0.1.0 -> E011 family -> E_pipelines -> 01_research -> SST-Workbench
for %%I in ("%~dp0..\..\..\..") do set "WB=%%~fI"
if defined SST_WORKBENCH_ROOT set "WB=%SST_WORKBENCH_ROOT%"
echo ============================================================
echo  E011 SKLSA v0.1.0 - selected low-crossing KnotPlot inventory
echo  Workbench: %WB%
echo ============================================================
python tools\run_inventory.py --workbench-root "%WB%" --mode selected
if errorlevel 1 exit /b %errorlevel%
echo [OK] Selected inventory complete.
