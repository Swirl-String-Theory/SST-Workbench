@echo off
setlocal EnableExtensions
cd /d "%~dp0" || exit /b 1
call "%~dp0run_install.cmd"
if errorlevel 1 endlocal & exit /b 1
set "PY=%~dp0.venv\Scripts\python.exe"
set "PYTEST=%~dp0.venv\Scripts\pytest.exe"
"%PYTEST%" -q
if errorlevel 1 endlocal & exit /b 1
"%PY%" tools\generate_demo.py
if errorlevel 1 endlocal & exit /b 1
"%PY%" -m sst_v_arrow_falsifier blind campaigns\demo_spectrum outputs_demo --config config\default.json --recursive --include-demo
if errorlevel 1 endlocal & exit /b 1
"%PY%" -m sst_v_arrow_falsifier freeze outputs_demo
if errorlevel 1 endlocal & exit /b 1
"%PY%" -m sst_v_arrow_falsifier plot outputs_demo
if errorlevel 1 endlocal & exit /b 1
endlocal & exit /b 0
