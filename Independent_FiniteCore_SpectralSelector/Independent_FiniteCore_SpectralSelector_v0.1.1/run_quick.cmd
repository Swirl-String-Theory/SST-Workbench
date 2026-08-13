@echo off
setlocal
cd /d "%~dp0"
python run_convergence_campaign.py --quick --threads 16 --q-min 2.31 --q-max 4.10 --q-step 0.05 --fine-q-step 0.005 --q-cluster-tol 0.03 --out-dir audit_quick %*
exit /b %ERRORLEVEL%
