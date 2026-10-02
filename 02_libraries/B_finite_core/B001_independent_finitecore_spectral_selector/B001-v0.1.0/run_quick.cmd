@echo off
setlocal
cd /d "%~dp0"
python run_blind_campaign.py --n-nodes 16 --ring-radius-over-core 4 --q-min 2.5 --q-max 12 --q-step 0.75 --image-shell 1 --fd-eps-over-core 5e-4 --core-model 0 --threads 16 --neutral-modes 6 --residual-max 0.1 --out-dir audit_quick %*
exit /b %ERRORLEVEL%
