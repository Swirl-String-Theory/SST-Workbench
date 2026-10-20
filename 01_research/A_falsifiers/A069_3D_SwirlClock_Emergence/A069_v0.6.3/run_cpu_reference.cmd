@echo off
setlocal
python gp_xpu_probe.py --device cpu --n 32 --steps 8 --out results\CPU_N32.json
exit /b %errorlevel%
