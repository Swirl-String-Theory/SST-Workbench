@echo off
setlocal
cd /d "%~dp0"
python run_fourier_convergence_campaign.py --quick --threads 16 --q-min 2.31 --q-max 2.60 --q-step 0.05 --max-m 12 --out-dir audit_fourier_probe %*
exit /b %ERRORLEVEL%
