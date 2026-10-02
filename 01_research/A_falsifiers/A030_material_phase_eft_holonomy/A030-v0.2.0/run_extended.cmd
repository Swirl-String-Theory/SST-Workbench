@echo off
setlocal
cd /d "%~dp0"
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
set "OUT=%~2"
if "%OUT%"=="" set "OUT=outputs\extended"
if not exist .venv call run_setup.cmd
if errorlevel 1 exit /b 1
call .venv\Scripts\activate.bat
python -m native_ext.build_ext_if_needed
if errorlevel 1 (
 echo [ERROR] EXTENDED requires native C++ extension.
 exit /b 1
)
echo ============================================================
echo EXTENDED blind + numerical-certification campaign
echo Dataset: %DATASET%
echo Output : %OUT%
echo ============================================================
python -m sst_eft_falsifier.campaign --config configs\extended.json --dataset "%DATASET%" --outdir "%OUT%"
set RC=%ERRORLEVEL%
endlocal & exit /b %RC%
