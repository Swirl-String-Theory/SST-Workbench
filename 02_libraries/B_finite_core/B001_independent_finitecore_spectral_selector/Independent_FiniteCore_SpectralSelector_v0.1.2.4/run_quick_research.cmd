@echo off
setlocal
cd /d "%~dp0"
python run_fourier_convergence_campaign.py --quick --threads 16 --q-min 2.31 --q-max 2.90 --q-step 0.025 --max-m 12 --symmetry-order 4 --q-cluster-tol 0.025 --q-gate-tol 0.020 --out-dir audit_fourier_quick_research %*
exit /b %ERRORLEVEL%
