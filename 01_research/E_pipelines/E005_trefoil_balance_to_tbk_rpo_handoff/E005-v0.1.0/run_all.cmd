@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "V48=..\SST_Trefoil_Lobe_Orientation_Blind_Falsifier\SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact\VERSION.json"
if exist "%V48%" goto RUN_V048
goto RUN_V046

:RUN_V048
call run_all_v048.cmd
exit /b %ERRORLEVEL%

:RUN_V046
echo [HANDOFF] v0.4.8 not found; falling back to v0.4.6.
call run_all_v046.cmd
exit /b %ERRORLEVEL%
