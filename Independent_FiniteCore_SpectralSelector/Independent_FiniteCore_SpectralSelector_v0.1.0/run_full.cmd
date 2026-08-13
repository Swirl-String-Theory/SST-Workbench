@echo off
setlocal
cd /d "%~dp0"
python run_blind_campaign.py --n-nodes 32 --ring-radius-over-core 4 --q-min 2.5 --q-max 40 --q-step 0.25 --image-shell 1 --fd-eps-over-core 1e-4 --core-model 0 --threads 16 --neutral-modes 6 --residual-max 0.05 --out-dir audit_full %*
exit /b %ERRORLEVEL%
