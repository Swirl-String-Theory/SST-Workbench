@echo off
setlocal
cd /d "%~dp0"
python bootstrap_upstream.py || exit /b 1
REM First grid-only refinement to B160; each run is an independent immutable output
python run_v062.py --case B192 --steps 16 --save-checkpoints || exit /b 1
python run_v062.py --case B256 --steps 16 --save-checkpoints || exit /b 1
REM Fourier A N512 may require 64-128 GiB RAM and many hours.
REM Run A512 manually after checking plan_v062.py (do NOT auto launch).
endlocal
