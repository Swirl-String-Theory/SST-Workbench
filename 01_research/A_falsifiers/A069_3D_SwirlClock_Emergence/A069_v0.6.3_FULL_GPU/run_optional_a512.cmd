@echo off
setlocal
cd /d "%~dp0"
if not defined A069_XPU_PYTHON set "A069_XPU_PYTHON=%~dp0.venv-xpu\Scripts\python.exe"
if not exist "%A069_XPU_PYTHON%" (echo Set A069_XPU_PYTHON to a tested XPU Python & exit /b 2)
echo WARNING: A512 can exceed 16 GB VRAM and take hours for source-native initialization. Check B256 peak and free VRAM first.
choice /C YN /M "Attempt A512 after VRAM safety guard"
if errorlevel 2 exit /b 1
"%A069_XPU_PYTHON%" gp_full_xpu.py --case A512 --init seed --total-steps 16 --diagnostic-every 4 --checkpoint-every 8 --cpu-parity-steps 0 --seed-chunk-planes 1
endlocal
