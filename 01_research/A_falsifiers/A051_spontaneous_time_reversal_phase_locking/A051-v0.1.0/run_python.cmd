@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m pytest -q
if errorlevel 1 exit /b %errorlevel%
set OUT=SST_Spontaneous_Time_Reversal_Phase_Locking_Blind_Falsifier_v0.1.0-outputs
python -m sst_trpl.cli synthetic --output-dir "%OUT%\blind\synthetic"
python -m sst_trpl.cli upstream-audit --snapshot data\upstream_evidence_snapshot.json --output "%OUT%\blind\upstream_readiness.json"
python tools\reveal.py --blind "%OUT%\blind\synthetic\blind_results.json" --snapshot data\upstream_evidence_snapshot.json --out "%OUT%\reveal\REVEAL_SUMMARY.json"
python tools\package_outputs.py --output-dir "%OUT%" --dest-prefix "..\%OUT%"
endlocal
