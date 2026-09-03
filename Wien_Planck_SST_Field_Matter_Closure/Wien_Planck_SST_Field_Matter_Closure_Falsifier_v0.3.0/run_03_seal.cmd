@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set "PY=.venv\Scripts\python.exe"
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0-outputs"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
if not exist "%OUTROOT%" mkdir "%OUTROOT%"
"%PY%" -c "from sst_wp.trust import seal; r=seal('.', r'Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0-outputs\runtime_code_seal.json'); print(r['commitment_sha256'])" || exit /b 1
popd
endlocal
