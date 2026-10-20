@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
if not defined PKLSA_WORKBENCH set "PKLSA_WORKBENCH=C:\workspace\projects\SST-Workbench"
if not defined PKLSA_PYTHON set "PKLSA_PYTHON=python"
set "ATLAS=%PKLSA_WORKBENCH%\01_research\E_pipelines"
set "E010=%ATLAS%\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.3.1\E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs.zip"
set "E011=%ATLAS%\E011_sklsa_selected_knot_link_seed_atlas\E011-v0.3.0\E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs.zip"
if defined PKLSA_E010_ZIP set "E010=%PKLSA_E010_ZIP%"
if defined PKLSA_E011_ZIP set "E011=%PKLSA_E011_ZIP%"
if exist "%E011%" set "PKLSA_TEST_E011_ZIP=%E011%"
if /I "%~1"=="SELFTEST" (
  "%PKLSA_PYTHON%" -m pytest -q tests\test_dynamics_v032.py
  exit /b !errorlevel!
)
if /I "%~1"=="BASIC" (
  "%PKLSA_PYTHON%" pklsa_dynamics_v032.py --workbench "%PKLSA_WORKBENCH%" --e011 "%E011%" --e010 "%E010%" --topology 3_1 --provider gilbert --fine-n 64 --steps 4 --basic --out "results"
  exit /b !errorlevel!
)
if /I "%~1"=="FULL" (
  "%PKLSA_PYTHON%" pklsa_dynamics_v032.py --workbench "%PKLSA_WORKBENCH%" --e011 "%E011%" --e010 "%E010%" --topology 3_1 --provider gilbert --fine-n 256 --steps 8 --out "results"
  exit /b !errorlevel!
)
echo Usage: run_dynamics_v032.cmd SELFTEST^|BASIC^|FULL
exit /b 2
