@echo off
setlocal
cd /d "%~dp0"
set "WB=%~1"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
call run_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_python.cmd -m a056_provider.campaign --config configs\provider_e010_filament_basic.json --workbench-root "%WB%"
if errorlevel 1 exit /b %ERRORLEVEL%
set "A056_INPUT_DIR=data\runtime_e010_filament_v040_m4"
set "A056_CONFIG=configs\e010_real_score.json"
call run_python.cmd run_instance.py FULL
if errorlevel 1 exit /b %ERRORLEVEL%
call run_python.cmd tools\print_gate_summary.py --output-dir A056_v0.4.0-outputs
if errorlevel 1 exit /b %ERRORLEVEL%
call run_python.cmd run_instance.py REVEAL_IF_ALLOWED
if errorlevel 1 exit /b %ERRORLEVEL%
call run_python.cmd tools\reveal_e010_provider.py --input-dir data\runtime_e010_filament_v040_m4 --output-dir A056_v0.4.0-outputs --require-framework-revealed
if errorlevel 1 exit /b %ERRORLEVEL%
call run_python.cmd tools\package_outputs.py
exit /b %ERRORLEVEL%
