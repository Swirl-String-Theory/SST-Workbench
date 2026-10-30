@echo off
setlocal EnableExtensions

rem upsert_polish_to_catalog.cmd — polish → uniform N300 → knotplot_knots_data.js
rem
rem   upsert_polish_to_catalog.cmd --from-outdir ..\knots\knot_3.1
rem   upsert_polish_to_catalog.cmd --polish path\to\…_polish.txt --outdir ..\knots\knot_3.1

set "BUNDLE=%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: python not found on PATH
  exit /b 1
)

python "%BUNDLE%upsert_polish_to_catalog.py" %*
exit /b %ERRORLEVEL%
