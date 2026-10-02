@echo off
setlocal
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set PYTHONPATH=%CD%

REM Prefer true machine-readable raw population data when present.
if exist "data\qgi\raw\fig2_population_raw.csv" goto :prepare

REM Otherwise acquire the fixed public manuscript unless explicitly disabled.
if exist "data\qgi\source\2502.14535v4.pdf" goto :prepare
if /I "%SST_QGI_NO_FETCH%"=="1" goto :prepare

echo No raw QGI CSV or local public PDF found.
echo Attempting fixed-source public QGI download for the CONDITIONAL Fig.2 fallback...
call run_fetch_qgi_public_pdf.cmd
if errorlevel 1 (
  echo WARNING: public QGI download failed. The pipeline will continue with QGI data status NOT_RUN.
)

:prepare
python -m sst_qgi.cli prepare-qgi --config configs\extended.json
if errorlevel 1 exit /b 1
endlocal
