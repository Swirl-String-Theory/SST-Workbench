@echo off
setlocal
cd /d "%~dp0"
call run_recover_campaign.cmd stage1_screen_30k_v2
exit /b %ERRORLEVEL%
