@echo off
setlocal
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\qhp"
set "OUT=%~2"
if "%OUT%"=="" set "OUT=outputs\basic"
call .venv\Scripts\activate.bat

if not exist "%DATASET%\qhp_metadata.csv" (
  echo [QHP] qhp_metadata.csv not found - trying strict filename inference...
  python -m sst_qhp_falsifier.cli metadata-bootstrap "%DATASET%"
  if errorlevel 2 (
    echo.
    echo [QHP] Metadata cannot be inferred safely from all filenames.
    echo [QHP] Template created: "%DATASET%\qhp_metadata_template.csv"
    echo [QHP] Fill q,h,p columns, save/copy as qhp_metadata.csv, then rerun run_all.cmd.
    exit /b 2
  )
  if errorlevel 1 exit /b 1
)

python -m sst_qhp_falsifier.cli prepare "%DATASET%" "%OUT%\prepared" config\basic.json --metadata "%DATASET%\qhp_metadata.csv" || exit /b 1
python -m sst_qhp_falsifier.cli run "%OUT%\prepared" "%OUT%\blind" config\basic.json || exit /b 1
python -m sst_qhp_falsifier.cli analyze "%OUT%\blind" "%OUT%\analysis" config\basic.json || exit /b 1
python -m sst_qhp_falsifier.cli reveal "%OUT%\prepared" "%OUT%\analysis" "%OUT%\reveal" || exit /b 1
