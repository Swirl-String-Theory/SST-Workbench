@echo off
setlocal
cd /d "%~dp0.."
where py >nul 2>&1
if errorlevel 1 (
  echo [F005] Python launcher py.exe not found.
  exit /b 2
)
py -3 -m unittest discover -s tests -p test_f005_v041.py -q
if errorlevel 1 (
  echo [F005] v0.4.1 synthetic regressions FAILED. No real-data run.
  exit /b 3
)
py -3 data\f005_free_run_family_v0.4.1.py --root . %*
if errorlevel 1 (
  echo [F005] v0.4.1 FAILED or blocked; inspect outputs.
  exit /b 4
)
echo [F005] v0.4.1 complete: outputs\f005_free_run_family_v0.4.1
endlocal
