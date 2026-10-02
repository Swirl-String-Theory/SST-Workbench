@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem Sequential paper-upgrade selftests in protocol order. Stop on first FAIL.
cd /d "%~dp0\.."
set WB=%CD%
set FAIL=0
set PASSN=0
set TOTAL=0

echo ============================================================
echo Paper-upgrade selftests (PU00 protocol order)
echo Workbench: %WB%
echo ============================================================

call :run D006 "01_research\D_benchmarks\D006_minimal_falsification_harness\D006-v0.4.0"
if errorlevel 1 goto :summary
call :run C006 "01_research\C_dynamics\C006_kelvin_floquet_workbench\C006-v0.2.0"
if errorlevel 1 goto :summary
call :run A037 "01_research\A_falsifiers\A037_chirality_helicity_transport_polarity\A037-v0.3.0"
if errorlevel 1 goto :summary
call :run A034 "01_research\A_falsifiers\A034_qhp_stability_landscape\A034-v0.2.0"
if errorlevel 1 goto :summary
call :run A029 "01_research\A_falsifiers\A029_finite_core_axial_toroidal_phase_delay\A029-v0.2.0"
if errorlevel 1 goto :summary
call :run A030 "01_research\A_falsifiers\A030_material_phase_eft_holonomy\A030-v0.2.0"
if errorlevel 1 goto :summary
call :run A023 "01_research\A_falsifiers\A023_multitopology_rpo_floquet\A023-v0.5.0"
if errorlevel 1 goto :summary
call :run A031 "01_research\A_falsifiers\A031_adaptive_period_rpo_floquet\A031-v0.2.0"
if errorlevel 1 goto :summary
call :run A035 "01_research\A_falsifiers\A035_intrinsic_modal_swirl_clock\A035-v0.3.0"
if errorlevel 1 goto :summary
call :run A008 "01_research\A_falsifiers\A008_chiral_kelvin_core\A008-v0.2.0"
if errorlevel 1 goto :summary
call :run A038 "01_research\A_falsifiers\A038_trefoil_dynamic_seed_qualification\A038-v0.4.0"
if errorlevel 1 goto :summary
call :run A021 "01_research\A_falsifiers\A021_trefoil_lobe_self_confinement\A021-v0.4.0"
if errorlevel 1 goto :summary
call :run A024 "01_research\A_falsifiers\A024_threaded_hole_separatrix\_variants\optional-paper-control"
if errorlevel 1 goto :summary
call :run A025 "01_research\A_falsifiers\A025_local_thread_texture_boost\_variants\optional-paper-control"
if errorlevel 1 goto :summary
call :run A016 "01_research\A_falsifiers\A016_helmholtz_vortex_transport\_variants\optional-paper-control"
if errorlevel 1 goto :summary
call :run A036 "01_research\A_falsifiers\A036_scii_intrinsic_modal_phase_clock\A036-v0.1.1"
if errorlevel 1 goto :summary
call :run A039 "01_research\A_falsifiers\A039_sciib_frozen_modal_pair_phase_clock\A039-v0.1.1"
if errorlevel 1 goto :summary
call :run A040 "01_research\A_falsifiers\A040_sciii_koopman_dmd_phase_clock\A040-v0.1.0"
if errorlevel 1 goto :summary

:summary
echo ============================================================
echo Result: !PASSN!/!TOTAL! PASS  FAIL=!FAIL!
echo ============================================================
if not "!FAIL!"=="0" exit /b 1
exit /b 0

:run
set ID=%~1
set REL=%~2
set /a TOTAL+=1
set DIR=%WB%\%REL%
if not exist "%DIR%\run_paper_upgrade.cmd" (
  echo [%ID%] FAIL  missing %DIR%\run_paper_upgrade.cmd
  set FAIL=1
  exit /b 1
)
pushd "%DIR%"
call run_paper_upgrade.cmd
set RC=!errorlevel!
popd
if not "!RC!"=="0" (
  echo [%ID%] FAIL  rc=!RC!
  set FAIL=1
  exit /b 1
)
echo [%ID%] PASS
set /a PASSN+=1
exit /b 0
