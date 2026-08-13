@echo off
setlocal
cd /d "%~dp0"
python run_fourier_convergence_campaign.py --threads 16 --q-min 2.31 --q-max 3.10 --q-step 0.01 --max-m 12 --symmetry-order 4 --q-cluster-tol 0.015 --q-gate-tol 0.010 --out-dir audit_fourier_convergence %*
exit /b %ERRORLEVEL%
