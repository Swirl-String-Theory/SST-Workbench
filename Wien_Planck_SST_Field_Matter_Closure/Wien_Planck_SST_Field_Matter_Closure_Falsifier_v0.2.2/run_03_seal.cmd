@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
"%PY%" -c "from sst_wp.trust import seal; r=seal('.', 'outputs/runtime_code_seal.json'); print(r['commitment_sha256'])" || exit /b 1
popd
endlocal
