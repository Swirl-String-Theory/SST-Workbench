@echo off
setlocal
call .venv\Scripts\activate.bat || exit /b 1
python -c "from sst_wp.trust import seal; r=seal('.', 'outputs/runtime_code_seal.json'); print(r['commitment_sha256'])" || exit /b 1
endlocal
