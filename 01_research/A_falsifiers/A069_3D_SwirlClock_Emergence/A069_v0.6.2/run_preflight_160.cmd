@echo off
setlocal
cd /d "%~dp0"
python bootstrap_upstream.py || exit /b 1
python run_v062.py --case B160 --steps 16 --diagnostic-every 8 --save-checkpoints || exit /b 1
REM Fourier A 160^3 is diagnostic-only: fails the core-separation/resolution conjunction.
python run_v062.py --case A160 --steps 16 --diagnostic-every 8 --allow-unqualified-geometry --save-checkpoints || exit /b 1
endlocal
