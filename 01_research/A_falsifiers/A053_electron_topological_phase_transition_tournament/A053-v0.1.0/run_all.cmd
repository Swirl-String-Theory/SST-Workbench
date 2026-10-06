@echo off
setlocal
cd /d "%~dp0"
set "WB=%~1"
set "OUT=A053_Electron_Topological_Phase_Transition_Tournament_v0.1.0-outputs"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
call run_python.cmd
if errorlevel 1 exit /b %errorlevel%
call run_plan.cmd "%WB%"
if errorlevel 1 echo [A053] Workbench plan has blockers; see %OUT%\WORKBENCH_PLAN.json
python -c "import shutil; shutil.make_archive(r'../A053_Electron_Topological_Phase_Transition_Tournament_v0.1.0-outputs_BLIND','zip',r'%OUT%')"
echo [A053] Blind evaluator qualification complete. Physical trajectories are never fabricated.
endlocal
