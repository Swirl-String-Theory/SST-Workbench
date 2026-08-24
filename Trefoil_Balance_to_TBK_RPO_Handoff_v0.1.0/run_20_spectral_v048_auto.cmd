@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo v0.4.8 adaptive spectral backend selection
echo ============================================================

call run_03_probe_v048_sycl.cmd
if not errorlevel 1 (
    echo [HANDOFF] DD32 worker available; using sycl-dd32.
    call run_20_spectral_v048_dd32.cmd
    if not errorlevel 1 exit /b 0
    echo [HANDOFF] DD32 execution failed despite a successful probe.
    echo [HANDOFF] Cleaning only the incomplete spectral stage and falling back to CPU/OpenMP.
) else (
    echo [HANDOFF] DD32 worker unavailable; using CPU/OpenMP spectral fallback.
)

if exist "tbk_outputs\v048\02_adaptive_spectral" rmdir /s /q "tbk_outputs\v048\02_adaptive_spectral"
if exist "tbk_outputs\v048\02_adaptive_spectral_HANDOFF_STAGE_RESULTS.json" del /q "tbk_outputs\v048\02_adaptive_spectral_HANDOFF_STAGE_RESULTS.json"

call run_20_spectral_v048_cpu.cmd
set "RC=%ERRORLEVEL%"
exit /b %RC%
