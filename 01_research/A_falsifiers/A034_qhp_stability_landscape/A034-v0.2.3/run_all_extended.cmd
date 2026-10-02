@echo off
setlocal
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\qhp"
echo ============================================================
echo SST QHP Stability Landscape Blind Falsifier v0.1.3
echo EXTENDED + resolution chain
echo Dataset: %DATASET%
echo ============================================================
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
call .venv\Scripts\activate.bat

if not exist "%DATASET%\qhp_metadata.csv" (
  echo [QHP] qhp_metadata.csv not found - trying strict filename inference...
  python -m sst_qhp_falsifier.cli metadata-bootstrap "%DATASET%"
  if errorlevel 2 (
    echo.
    echo [QHP] Metadata cannot be inferred safely from all filenames.
    echo [QHP] Template created: "%DATASET%\qhp_metadata_template.csv"
    echo [QHP] Fill q,h,p columns, save/copy as qhp_metadata.csv, then rerun run_all_extended.cmd.
    exit /b 2
  )
  if errorlevel 1 exit /b 1
)

python -m sst_qhp_falsifier.cli prepare "%DATASET%" outputs\extended\prepared config\extended.json --metadata "%DATASET%\qhp_metadata.csv" || exit /b 1
python -m sst_qhp_falsifier.cli run outputs\extended\prepared outputs\extended\blind config\extended.json || exit /b 1
python -m sst_qhp_falsifier.cli analyze outputs\extended\blind outputs\extended\analysis config\extended.json || exit /b 1
python -m sst_qhp_falsifier.cli reveal outputs\extended\prepared outputs\extended\analysis outputs\extended\reveal || exit /b 1
for %%N in (64 96 128) do (
  python -m sst_qhp_falsifier.cli prepare "%DATASET%" outputs\resolution_N%%N\prepared config\resolution_N%%N.json --metadata "%DATASET%\qhp_metadata.csv" || exit /b 1
  python -m sst_qhp_falsifier.cli run outputs\resolution_N%%N\prepared outputs\resolution_N%%N\blind config\resolution_N%%N.json || exit /b 1
  python -m sst_qhp_falsifier.cli analyze outputs\resolution_N%%N\blind outputs\resolution_N%%N\analysis config\resolution_N%%N.json || exit /b 1
  python -m sst_qhp_falsifier.cli reveal outputs\resolution_N%%N\prepared outputs\resolution_N%%N\analysis outputs\resolution_N%%N\reveal || exit /b 1
)
python -m sst_qhp_falsifier.resolution outputs resolution_N64 resolution_N96 resolution_N128 outputs\RESOLUTION_SUMMARY.json || exit /b 1
echo DONE: outputs\extended + resolution ladder
