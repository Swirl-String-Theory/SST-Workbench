@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist "data\f005_free_run_family_v0.4.1.py" (
  echo [F005 v0.4.3] Missing installed v0.4.1 dependency.
  exit /b 2
)
if not exist "outputs\f005_qualification_v0.4.2\v042_report.json" (
  echo [F005 v0.4.3] v0.4.2 results required.
  exit /b 2
)
if not exist "outputs\f005_qualification_v0.4.2\family_candidate_matches_REVIEW.csv" (
  echo [F005 v0.4.3] v0.4.2 family match CSV required.
  exit /b 2
)
py -3 -m unittest discover -s tests -p test_v043.py -v
if errorlevel 1 exit /b 3
py -3 "data\f005_family_disjoint_v0.4.3.py" --root "%CD%"
if errorlevel 1 exit /b 4
echo [F005 v0.4.3] Development run complete. TEST/OOD response sealed.
exit /b 0
