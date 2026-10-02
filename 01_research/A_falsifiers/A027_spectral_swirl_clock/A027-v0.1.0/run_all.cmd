@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_all.cmd ^<campaign_dir^> [outdir]
  echo This intentionally STOPS before unblinding.
  exit /b 2
)
call run_install.cmd || exit /b 1
call .venv\Scripts\activate.bat
python -m sst_v_arrow_falsifier audit --root . || exit /b 1
pytest -q || exit /b 1
call run_blind.cmd "%~1" "%~2" || exit /b 1
echo.
echo ============================================================
echo BLIND PHASE COMPLETE AND HASH-LOCKED.
echo Inspect the blind report first. Then run: run_unblind.cmd ^<outdir^>
echo ============================================================
endlocal
