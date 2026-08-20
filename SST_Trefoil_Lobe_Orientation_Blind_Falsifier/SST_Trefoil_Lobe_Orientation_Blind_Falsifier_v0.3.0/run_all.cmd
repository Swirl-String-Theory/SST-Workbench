@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo SST Trefoil Coupled TBK + RPO/Floquet Falsifier v0.3.0
echo ============================================================
call run_install.cmd || exit /b 1
call run_test.cmd || exit /b 1
call run_basic.cmd %*
set BASIC_RC=%errorlevel%
call run_extended.cmd %*
set EXT_RC=%errorlevel%
echo ============================================================
echo Completed. BASIC rc=%BASIC_RC% EXTENDED rc=%EXT_RC%
echo Scientific FAIL is a valid completed result; INCONCLUSIVE returns rc=2.
echo ============================================================
if %BASIC_RC%==2 exit /b 2
if %EXT_RC%==2 exit /b 2
exit /b 0
