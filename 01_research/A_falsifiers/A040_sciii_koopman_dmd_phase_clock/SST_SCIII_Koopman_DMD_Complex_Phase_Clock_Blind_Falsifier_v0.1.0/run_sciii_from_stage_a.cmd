@echo off
setlocal EnableExtensions
set WORK=%~1
if "%WORK%"=="" set WORK=outputs\basic
set CFG=%~2
if "%CFG%"=="" set CFG=config\basic.json
echo ============================================================
echo SST SC-III v0.1.0 - reuse existing Stage-A trajectories
echo Local Koopman/DMD moving-subspace complex phase clock
echo Work:   %WORK%
echo Config: %CFG%
echo No Stage-A physics will be recomputed.
echo ============================================================
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
call .venv\Scripts\activate.bat || exit /b 1
if not exist "%WORK%\results_stage_a\candidates" (
  echo ERROR: missing %WORK%\results_stage_a\candidates
  exit /b 2
)
echo [1/8] Analyze existing Stage A for SC-III Koopman/DMD candidates
python -m sst_modal_clock.cli analyze-sciii-stage-a "%WORK%" "%CFG%" || exit /b 1
echo [2/8] LOW mesh-gauge replay on provisional candidates only
python -m sst_modal_clock.cli run "%WORK%" "%CFG%" --branch stage_a_gauge_low || exit /b 1
echo [3/8] HIGH mesh-gauge replay on provisional candidates only
python -m sst_modal_clock.cli run "%WORK%" "%CFG%" --branch stage_a_gauge_high || exit /b 1
echo [4/8] SC-III mesh-gauge certification
python -m sst_modal_clock.cli analyze-sciii-gauge "%WORK%" "%CFG%" || exit /b 1
echo [5/8] SC-III provenance robustness
python -m sst_modal_clock.cli analyze-sciii-provenance "%WORK%" "%CFG%" || exit /b 1
echo [6/8] Material-core Stage B on certified candidates
python -m sst_modal_clock.cli run "%WORK%" "%CFG%" --branch material || exit /b 1
echo [7/8] Fixed-core Stage B null
python -m sst_modal_clock.cli run "%WORK%" "%CFG%" --branch fixed || exit /b 1
echo [8/8] SC-III causal phase analysis
python -m sst_modal_clock.cli analyze-sciii-stage-b "%WORK%" "%CFG%" || exit /b 1
echo.
echo Result: %WORK%\analysis\blind_sciii_summary.json
