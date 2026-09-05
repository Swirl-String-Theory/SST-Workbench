@echo off
setlocal
cd /d "%~dp0"
python run_convergence_campaign.py --threads 16 --q-min 2.31 --q-max 4.10 --q-step 0.025 --fine-q-step 0.0025 --q-cluster-tol 0.02 --out-dir audit_convergence %*
exit /b %ERRORLEVEL%
