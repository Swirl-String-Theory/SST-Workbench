@echo off
setlocal
set OUT=outputs\focus_provenance_3p1
if exist "%OUT%" rmdir /s /q "%OUT%"
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
call .venv\Scripts\activate.bat || exit /b 1
echo ============================================================
echo v0.2.2.6 K3.1 seed-provenance focus
echo selected libraries; recommended Fremlin vs Gilbert vs Katlas
 echo ============================================================
python -m sst_modal_clock.cli prepare-provenance "%OUT%" config\provenance_focus_3p1.json %* || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\provenance_focus_3p1.json --branch stage_a || exit /b 1
python -m sst_modal_clock.cli analyze-stage-a "%OUT%" config\provenance_focus_3p1.json || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\provenance_focus_3p1.json --branch stage_a_gauge_low || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\provenance_focus_3p1.json --branch stage_a_gauge_high || exit /b 1
python -m sst_modal_clock.cli analyze-stage-a-gauge "%OUT%" config\provenance_focus_3p1.json || exit /b 1
python -m sst_modal_clock.cli analyze-provenance "%OUT%" config\provenance_focus_3p1.json || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\provenance_focus_3p1.json --branch material || exit /b 1
python -m sst_modal_clock.cli run "%OUT%" config\provenance_focus_3p1.json --branch fixed || exit /b 1
python -m sst_modal_clock.cli analyze-stage-b "%OUT%" config\provenance_focus_3p1.json || exit /b 1
echo Result: %OUT%\analysis\blind_provenance_summary.json
