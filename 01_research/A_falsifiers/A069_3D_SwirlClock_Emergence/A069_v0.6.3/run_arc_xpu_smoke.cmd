@echo off
setlocal
REM Execute in a dedicated XPU-enabled Python environment.
REM No fallback to CPU. Fails explicitly if A770 or complex 3D FFT missing.
python gp_xpu_probe.py --device xpu --expected-name A770 --n 32 --steps 8 --out results\A770_N32.json
if errorlevel 1 exit /b %errorlevel%
python gp_xpu_probe.py --device xpu --expected-name A770 --n 64 --steps 8 --out results\A770_N64.json
exit /b %errorlevel%
