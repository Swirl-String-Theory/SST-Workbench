@echo off
setlocal
cd /d "%~dp0"
call run_install.cmd || exit /b 1
call .venv\Scripts\activate.bat
python tools\generate_demo.py || exit /b 1
call run_blind.cmd campaigns\demo_spectrum outputs_demo || exit /b 1
python -m sst_v_arrow_falsifier unblind outputs_demo --target sealed\unblind_target.json --config config\default.json
endlocal
