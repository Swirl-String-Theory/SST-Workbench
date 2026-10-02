@echo off
setlocal
cd /d "%~dp0\.."
set PYTHONPATH=%CD%\src;%PYTHONPATH%
py examples\generate_synthetic_fixture.py || exit /b 1
py -m sst_maxwell_blind.cli run --config config\preregister.json --campaign examples\synthetic_campaign\campaign.csv --reduced-momentum examples\synthetic_campaign\reduced_momentum.csv --storage examples\synthetic_campaign\storage_current.npz --outdir examples\synthetic_campaign\results_blind
