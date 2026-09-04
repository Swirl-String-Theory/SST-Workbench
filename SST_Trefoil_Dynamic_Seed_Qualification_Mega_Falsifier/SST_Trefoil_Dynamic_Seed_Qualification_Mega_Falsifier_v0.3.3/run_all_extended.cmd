@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set DATA=%~1
if "%DATA%"=="" (
  echo A fresh held-out trefoil atlas path is required for a scientific run.
  echo Example: run_all.cmd C:\path\to\held_out_trefoil_atlas
  exit /b 2
)
set ROOTOUT=SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.3-outputs
set OUT=%ROOTOUT%\extended
set CFG=config\extended.json
echo ============================================================
echo SST Trefoil Dynamic Seed Qualification Mega Falsifier v0.3.3
echo EXTENDED operator-split arclength-remap chain
echo Dataset: %DATA%
echo S10 source atlas ^> S20 rolling ^> S25 refine ^> S30 spatial
echo ^> S32 temporal ^> S35 core ^> S37A legacy mesh gauge
echo ^> S37B closure diagnostic ^> S37C operator-split certification
echo ^> S40 long ^> S50 projected Floquet ^> S60 mechanism ^> S70 reveal
echo ============================================================
call run_00_setup.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_02_selftest.cmd || exit /b 1
call run_10_prepare.cmd "%DATA%" "%OUT%" "%CFG%" || exit /b 1
call run_20_early.cmd "%OUT%" "%CFG%" || exit /b 1
call run_25_refine.cmd "%OUT%" "%CFG%" || exit /b 1
call run_30_resolution.cmd "%OUT%" "%CFG%" || exit /b 1
call run_32_temporal.cmd "%OUT%" "%CFG%" || exit /b 1
call run_35_core.cmd "%OUT%" "%CFG%" || exit /b 1
call run_37_mesh_gauge.cmd "%OUT%" "%CFG%" || exit /b 1
call run_37b_mesh_closure.cmd "%OUT%" "%CFG%" || exit /b 1
call run_37c_operator_split.cmd "%OUT%" "%CFG%" || exit /b 1
call run_40_long.cmd "%OUT%" "%CFG%" || exit /b 1
call run_50_rpo.cmd "%OUT%" "%CFG%" || exit /b 1
call run_60_mechanism.cmd "%OUT%" "%CFG%" || exit /b 1
call _common.cmd
"%PY%" -m sst_seed_falsifier.archive blind "%ROOTOUT%" || exit /b 1
call run_70_reveal.cmd "%OUT%" || exit /b 1
"%PY%" -m sst_seed_falsifier.archive revealed "%ROOTOUT%" || exit /b 1
echo ============================================================
echo EXTENDED chain complete.
echo Inspect: %OUT%\BLIND_CHAIN_SUMMARY.json
echo          %OUT%\stage37c_operator_split_remap\summary.json
echo          %OUT%\REVEAL_SUMMARY.json
echo Shareable *_BLIND.zip and *_REVEALED.zip were written one directory above this project.
echo ============================================================
