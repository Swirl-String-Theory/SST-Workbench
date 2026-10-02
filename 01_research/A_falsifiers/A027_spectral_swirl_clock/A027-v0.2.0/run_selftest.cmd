@echo off
setlocal
cd /d "%~dp0"
call run_install.cmd || exit /b 1
call .venv\Scripts\activate.bat
pytest -q || exit /b 1
python tools\generate_demo.py || exit /b 1
python -m sst_v_arrow_falsifier blind campaigns\demo_spectrum outputs_demo --config config\default.json --recursive --include-demo || exit /b 1
python -m sst_v_arrow_falsifier freeze outputs_demo || exit /b 1
python -m sst_v_arrow_falsifier plot outputs_demo
endlocal
