@echo off
setlocal
cd /d "%~dp0"
python bootstrap_upstream.py || exit /b 1
REM Core-scale variation (xi 0.24), not directly the same experiment as xi 0.28.
python run_v062.py --case B192_CORE024 --steps 16 --save-checkpoints || exit /b 1
python run_v062.py --case B256_CORE024 --steps 16 --save-checkpoints || exit /b 1
endlocal
