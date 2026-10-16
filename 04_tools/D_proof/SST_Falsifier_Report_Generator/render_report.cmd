@echo off
setlocal
if "%~5"=="" (
 echo Usage: render_report.cmd SOURCE_OUTPUTS DEST_REPORTS CATALOG VERSION "TITLE"
 echo Example: render_report.cmd "C:\path\A054-v0.5.1\...-outputs" "C:\reports" A054 v0.5.1 "State-selection"
 exit /b 2
)
set "SCRIPT=%~dp0report_generator.py"
py -3 "%SCRIPT%" --outputs "%~1" --dest "%~2" --catalog "%~3" --version "%~4" --title "%~5"
exit /b %errorlevel%
