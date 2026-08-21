@echo off
setlocal
cd /d "%~dp0"
call .venv\Scripts\activate.bat
pytest -q
python tools\generate_demo.py
python -m sst_v_arrow_falsifier blind campaigns\demo_spectrum outputs_demo --config config\default.json
python -m sst_v_arrow_falsifier freeze outputs_demo
python -m sst_v_arrow_falsifier plot outputs_demo
endlocal
