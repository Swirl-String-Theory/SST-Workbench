@echo off
setlocal
set "SOURCE=%~dp0..\E010-v0.3.1\E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs"
python "%~dp0build_multiseed_view.py" --source "%SOURCE%" --dry-run
if errorlevel 1 exit /b %errorlevel%
echo.
echo Dry run completed. Run the Python script without --dry-run to create the view.
