@echo off
setlocal
cd /d "%~dp0"
if not exist build\Release\sst_reciprocal_core.exe if not exist build\sst_reciprocal_core.exe call build_native.cmd || exit /b 1
if exist example_blind rmdir /s /q example_blind
if exist example_private_key.json del /q example_private_key.json
python python\prepare_blind.py examples\datasets.private.example.json --out example_blind --private-key example_private_key.json || exit /b 1
python python\run_blind.py example_blind || exit /b 1
python python\unblind.py example_blind\results example_private_key.json --out example_unblinded_summary.json || exit /b 1
echo Done. See example_blind\results and example_unblinded_summary.json
