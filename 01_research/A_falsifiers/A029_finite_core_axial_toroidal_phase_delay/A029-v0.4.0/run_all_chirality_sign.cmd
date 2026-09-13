@echo off
call "%~dp0run_chirality_sign_prepare.cmd" || exit /b 1
call "%~dp0run_chirality_sign_blind.cmd" || exit /b 1
call "%~dp0run_chirality_sign_reveal.cmd" || exit /b 1
