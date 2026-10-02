@echo off
setlocal
cd /d "%~dp0"
if not exist .venv call run_setup.cmd
call .venv\Scripts\activate.bat
python tools\generate_synthetic_dataset.py
python -m sst_eft_falsifier.campaign --config configs\basic.json --dataset "_synthetic_dataset" --outdir "outputs\smoke"
endlocal
