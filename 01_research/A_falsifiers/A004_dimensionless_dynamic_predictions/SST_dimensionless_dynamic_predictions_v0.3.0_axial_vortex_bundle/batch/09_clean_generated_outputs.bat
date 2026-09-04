@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
echo Dit verwijdert alleen de door de batchscripts gemaakte uitvoermappen:
echo   outputs\quick_batch
 echo   outputs\static_diagnostics
 echo   outputs\single_evolution
 echo   outputs\medium_campaign
 echo   outputs\research_campaign
choice /M "Doorgaan"
if errorlevel 2 exit /b 0
for %%D in (quick_batch static_diagnostics single_evolution medium_campaign research_campaign) do (
    if exist "outputs\%%D" rmdir /s /q "outputs\%%D"
)
echo [OK] Gegenereerde uitvoer verwijderd.
pause
