@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo SST Multi-Topology Knot/Link TBK + RPO/Floquet v0.4.8
echo ============================================================
echo [SST] run_all uses confirmatory CPU/OpenMP FP64 only.
echo [SST] For Arc/SYCL use run_sycl_worker_smoke.cmd or *_sycl.cmd explicitly.
call run_install.cmd
if errorlevel 1 exit /b %errorlevel%
call run_panel_basic.cmd
set BASIC_RC=%errorlevel%
call run_panel_extended.cmd
set EXT_RC=%errorlevel%
echo ============================================================
echo Completed. BASIC rc=%BASIC_RC% EXTENDED rc=%EXT_RC%
echo PASS/FAIL are scientific classifications; script errors are separate.
echo ============================================================
if not "%EXT_RC%"=="0" exit /b %EXT_RC%
exit /b %BASIC_RC%
