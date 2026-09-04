@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo SST v0.4.5.3 FULL ARCHIVE: validate + EXTRA_EXTENDED + FULL
echo ============================================================
call run_install.cmd || exit /b 1
call run_archive_validate.cmd || exit /b 1
call run_archive_extra_extended.cmd
set EXTRA_RC=%errorlevel%
call run_archive_full.cmd
set FULL_RC=%errorlevel%
echo ============================================================
echo Completed. EXTRA_EXTENDED rc=%EXTRA_RC% FULL rc=%FULL_RC%
echo ============================================================
if not "%FULL_RC%"=="0" exit /b %FULL_RC%
exit /b %EXTRA_RC%
