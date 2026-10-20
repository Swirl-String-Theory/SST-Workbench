@echo off
setlocal
cd /d "%~dp0"
python bootstrap_upstream.py || exit /b 1
REM B160 constant T=0.048; halve dt and double steps. Separate immutable result.
python run_v062.py --case B160 --dt 0.0015 --steps 32 --diagnostic-every 16 --save-checkpoints || exit /b 1
endlocal
