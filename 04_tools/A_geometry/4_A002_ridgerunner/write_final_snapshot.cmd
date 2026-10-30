@echo off
setlocal EnableExtensions

rem write_final_snapshot.cmd — copy polish → unique *_final_* snapshot
rem
rem   write_final_snapshot.cmd --polish path\to\…_polish.txt --stem build_knot_3.1 --tag min
rem   write_final_snapshot.cmd --from-outdir out\3_1 --stem 3_1 --tag N900 --suffix scout

set "BUNDLE=%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: python not found on PATH
  exit /b 1
)

python "%BUNDLE%write_final_snapshot.py" %*
exit /b %ERRORLEVEL%
