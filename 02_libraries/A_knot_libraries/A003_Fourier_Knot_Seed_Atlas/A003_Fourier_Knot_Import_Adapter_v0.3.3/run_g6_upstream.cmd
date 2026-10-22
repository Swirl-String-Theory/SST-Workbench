@echo off
setlocal EnableExtensions
set "ADAPTER_ROOT=%~dp0"
set "WORKBENCH=C:\workspace\projects\SST-Workbench"
if defined SST_WORKBENCH_ROOT set "WORKBENCH=%SST_WORKBENCH_ROOT%"
set "E010_ROOT=%WORKBENCH%\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.3.2"
if defined SST_E010_ROOT set "E010_ROOT=%SST_E010_ROOT%"
set "A058_ROOT=%WORKBENCH%\01_research\A_falsifiers\A058_KnotPlot_Parameter_Sensitivity_Relaxation_Robustness\A058-v0.3.2"
if defined SST_A058_ROOT set "A058_ROOT=%SST_A058_ROOT%"
set "FRAMEWORK_ROOT=%WORKBENCH%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10"
if defined SST_FRAMEWORK_ROOT set "FRAMEWORK_ROOT=%SST_FRAMEWORK_ROOT%"
set "C005_ROOT=%WORKBENCH%\01_research\C_dynamics\C005_fermat_biot_savart\C005-v0.6.1"
if defined SST_C005_ROOT set "C005_ROOT=%SST_C005_ROOT%"
python "%ADAPTER_ROOT%g6_upstream_v033.py" --workbench "%WORKBENCH%" --e010 "%E010_ROOT%" --a058 "%A058_ROOT%" --c005 "%C005_ROOT%" --framework "%FRAMEWORK_ROOT%" %*
exit /b %ERRORLEVEL%
