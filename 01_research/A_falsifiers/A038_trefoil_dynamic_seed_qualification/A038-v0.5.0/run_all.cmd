@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo [paper-upgrade] gate selftest
call "%~dp0run_paper_upgrade.cmd" || exit /b 1

rem --- paper-upgrade resume/heartbeat (PU01b) ---
set "PU_FAMILY=A038"
set "PU_TIER=basic"
rem Runtime markers live under outputs\basic; campaign evidence stays in ROOTOUT\basic.
set "PU_OUT=outputs\basic"
echo.%*| findstr /I /C:"/resume" >nul && set "SST_RESUME=1"
echo.%*| findstr /I /C:"/fresh" >nul && set "SST_FRESH=1"
for /f "delims=" %%W in ('python -c "from pathlib import Path;import sys;p=Path.cwd().resolve();cs=[p,*p.parents];ok=[c for c in cs if (c/'07_scripts'/'paper_upgrade_runtime.py').is_file()];print(ok[0] if ok else '');sys.exit(0 if ok else 2)"') do set "PU_WB=%%W"
if not defined PU_WB (echo [paper-upgrade] ERROR: workbench root not found & exit /b 2)
set "PU_RESUME_FLAG="
if /I "%SST_RESUME%"=="1" set "PU_RESUME_FLAG=--resume"
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" init --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" %PU_RESUME_FLAG% || exit /b 1
set DATA=%~1
if "%DATA%"=="" (
  if defined SST_A038_DATASET (
    set "DATA=%SST_A038_DATASET%"
  ) else if defined SST_ATLAS_ROOT (
    rem Do not reuse SST_ATLAS_ROOT here — A031 atlases are not A038 trefoil source sets.
    set "DATA=%PU_WB%\01_research\A_falsifiers\A038_trefoil_dynamic_seed_qualification\A038-v0.3.0\outputs\prospective_atlas_v030\test_atlas"
  ) else (
    set "DATA=%PU_WB%\01_research\A_falsifiers\A038_trefoil_dynamic_seed_qualification\A038-v0.3.0\outputs\prospective_atlas_v030\test_atlas"
  )
)
if not exist "%DATA%" (
  echo A fresh held-out trefoil atlas path is required for a scientific run.
  echo Example: run_all.cmd C:\path\to\held_out_trefoil_atlas
  echo Missing: %DATA%
  exit /b 2
)
set ROOTOUT=SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.5.0-outputs
set OUT=%ROOTOUT%\basic
set CFG=config\basic.json
echo ============================================================
echo SST Trefoil Dynamic Seed Qualification Mega Falsifier v0.5.0
echo BASIC operator-split arclength-remap chain
echo Dataset: %DATA%
echo S10 source atlas ^> S20 rolling ^> S25 refine ^> S30 spatial
echo ^> S32 temporal ^> S35 core ^> S37A legacy mesh gauge
echo ^> S37B closure diagnostic ^> S37C operator-split certification
echo ^> S40 long ^> S50 projected Floquet ^> S60 mechanism ^> S70 reveal
echo ============================================================
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "00_setup" %PU_RESUME_FLAG% -- run_00_setup.cmd || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "01_build_native" %PU_RESUME_FLAG% -- run_01_build_native.cmd || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "02_selftest" %PU_RESUME_FLAG% -- run_02_selftest.cmd || exit /b 1
if not defined SST_A034_CERT set "SST_A034_CERT=%PU_WB%\01_research\A_falsifiers\A034_qhp_stability_landscape\A034-v0.2.1\outputs\basic\paper_upgrade\certificate.json"
if not defined SST_A037_CERT set "SST_A037_CERT=%PU_WB%\01_research\A_falsifiers\A037_chirality_helicity_transport_polarity\A037-v0.3.1\outputs\basic\paper_upgrade\certificate.json"
python "%PU_WB%\07_scripts\paper_upgrade_certs.py" write-a038-upstream --out "%PU_OUT%" --a034 "%SST_A034_CERT%" --a037 "%SST_A037_CERT%" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "upstream_gate" %PU_RESUME_FLAG% -- python "%PU_WB%\07_scripts\paper_upgrade_certs.py" upstream-a038 --certs "%PU_OUT%\paper_upgrade\upstream_certs.json" --gate "paper_upgrade\gate.py" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "10_prepare" %PU_RESUME_FLAG% -- run_10_prepare.cmd "%DATA%" "%OUT%" "%CFG%" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "20_early" %PU_RESUME_FLAG% -- run_20_early.cmd "%OUT%" "%CFG%" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "25_refine" %PU_RESUME_FLAG% -- run_25_refine.cmd "%OUT%" "%CFG%" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "30_resolution" %PU_RESUME_FLAG% -- run_30_resolution.cmd "%OUT%" "%CFG%" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "32_temporal" %PU_RESUME_FLAG% -- run_32_temporal.cmd "%OUT%" "%CFG%" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "35_core" %PU_RESUME_FLAG% -- run_35_core.cmd "%OUT%" "%CFG%" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "37_mesh_gauge" %PU_RESUME_FLAG% -- run_37_mesh_gauge.cmd "%OUT%" "%CFG%" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "37b_mesh_closure" %PU_RESUME_FLAG% -- run_37b_mesh_closure.cmd "%OUT%" "%CFG%" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "37c_operator_split" %PU_RESUME_FLAG% -- run_37c_operator_split.cmd "%OUT%" "%CFG%" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "40_long" %PU_RESUME_FLAG% -- run_40_long.cmd "%OUT%" "%CFG%" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "50_rpo" %PU_RESUME_FLAG% -- run_50_rpo.cmd "%OUT%" "%CFG%" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "60_mechanism" %PU_RESUME_FLAG% -- run_60_mechanism.cmd "%OUT%" "%CFG%" || exit /b 1
call _common.cmd
"%PY%" -m sst_seed_falsifier.archive blind "%ROOTOUT%" || exit /b 1
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "70_reveal" %PU_RESUME_FLAG% -- run_70_reveal.cmd "%OUT%" || exit /b 1
"%PY%" -m sst_seed_falsifier.archive revealed "%ROOTOUT%" || exit /b 1
echo ============================================================
echo BASIC chain complete.
echo Inspect: %OUT%\BLIND_CHAIN_SUMMARY.json
echo          %OUT%\stage37c_operator_split_remap\summary.json
echo          %OUT%\REVEAL_SUMMARY.json
echo Shareable *_BLIND.zip and *_REVEALED.zip were written one directory above this project.
echo ============================================================
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" finish --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --status DONE
