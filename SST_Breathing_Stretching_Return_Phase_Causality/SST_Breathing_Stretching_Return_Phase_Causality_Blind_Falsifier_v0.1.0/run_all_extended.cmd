@echo off
setlocal
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
echo ============================================================
echo SST Breathing-Stretching-Return-Phase Causality Falsifier v0.1.1
echo EXTENDED blind chain
echo Dataset: %DATASET%
echo ============================================================
call run_setup.cmd || goto :fail
call run_build_native.cmd || goto :fail
call run_selftest.cmd || goto :fail
call .venv\Scripts\activate.bat
python -m sst_bsrp_falsifier.cli prepare "%DATASET%" outputs\extended config\extended.json || goto :fail
call run_extended.cmd outputs\extended || goto :fail
echo Running fixed-core stretching null...
call run_stretch_null.cmd "%DATASET%" || goto :fail
echo Blind extended + stretch-mediation score complete. Reveal remains separate:
echo   run_reveal.cmd outputs\extended
exit /b 0
:fail
exit /b 1
