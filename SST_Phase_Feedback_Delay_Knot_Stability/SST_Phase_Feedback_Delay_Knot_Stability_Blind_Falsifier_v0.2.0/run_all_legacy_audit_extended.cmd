@echo off
call "%~dp0run_all_legacy_audit.cmd" "%~1" extended
exit /b %ERRORLEVEL%
