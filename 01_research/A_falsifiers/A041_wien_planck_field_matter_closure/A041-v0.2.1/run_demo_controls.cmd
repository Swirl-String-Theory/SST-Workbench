@echo off
setlocal
if not exist .venv call run_00_setup.cmd || exit /b 1
call .venv\Scripts\activate.bat || exit /b 1
if not exist demo mkdir demo
python -m sst_wp.blind_guard || exit /b 1
python -m sst_wp.synthetic_controls action-positive demo\action_positive.csv
python -m sst_wp.synthetic_controls action-classical demo\action_classical.csv
python -m sst_wp.synthetic_controls closure-positive demo\closure_positive.csv
python -m sst_wp.synthetic_controls closure-negative demo\closure_negative.csv
python -m sst_wp.action_prepare demo\action_positive.csv --out-dir outputs\demo_positive --private-dir private_reveal_keys
python -m sst_wp.action_analyze outputs\demo_positive\BLIND_INPUT.csv --config config\basic.json --out outputs\demo_positive\BLIND_RESULTS.json
python -m sst_wp.action_prepare demo\action_classical.csv --out-dir outputs\demo_classical --private-dir private_reveal_keys
python -m sst_wp.action_analyze outputs\demo_classical\BLIND_INPUT.csv --config config\basic.json --out outputs\demo_classical\BLIND_RESULTS.json
python -m sst_wp.closure_analyze demo\closure_positive.csv --config config\basic.json --out outputs\demo_closure_positive.json
python -m sst_wp.closure_analyze demo\closure_negative.csv --config config\basic.json --out outputs\demo_closure_negative.json
echo Synthetic controls complete. They are pipeline tests only.
endlocal
