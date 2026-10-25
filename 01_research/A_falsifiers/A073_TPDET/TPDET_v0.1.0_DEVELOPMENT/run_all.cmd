@echo off
setlocal
cd /d "%~dp0"
python -m pytest -q tests || exit /b 1
python euler_energy_flux.py --out output\TPDET_v0.1.0_euler_control.json || exit /b 1
python tpdet.py --n 128 --dt 0.015 --t-end 8 --core 0.12 --record-every 10 --out output\TPDET_v0.1.0_LOCAL_NEW || exit /b 1
exit /b 0
