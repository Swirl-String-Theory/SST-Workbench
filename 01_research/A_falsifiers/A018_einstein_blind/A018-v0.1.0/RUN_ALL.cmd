@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo Einstein-SST Blind Falsifier v0.1.0 - STANDARD
echo Gate order: E3 ^> E4 ^> E5 ^> E2 ^> E1
echo Target-free evaluator: no h, hbar, c or alpha benchmark.
echo ============================================================
call "%~dp0run_all_standard.cmd"
exit /b %errorlevel%
