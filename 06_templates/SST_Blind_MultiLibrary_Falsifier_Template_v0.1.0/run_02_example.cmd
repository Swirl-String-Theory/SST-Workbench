@echo off
setlocal
call .venv\Scripts\activate.bat
python run_pipeline.py --config configs\basic.json --out SST_Blind_MultiLibrary_Falsifier_Template_v0.1.0-outputs\basic
