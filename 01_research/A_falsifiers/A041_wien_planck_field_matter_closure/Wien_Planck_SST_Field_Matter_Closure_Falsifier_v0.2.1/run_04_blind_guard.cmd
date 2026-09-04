@echo off
setlocal
call .venv\Scripts\activate.bat || exit /b 1
if not exist outputs mkdir outputs
python -m sst_wp.blind_guard --out outputs\BLIND_CODE_AUDIT.json || exit /b 1
echo Blind constant/SI leakage guard: PASS
endlocal
