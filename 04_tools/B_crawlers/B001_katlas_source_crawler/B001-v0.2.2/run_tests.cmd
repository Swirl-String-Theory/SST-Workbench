@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3 -m venv .venv || exit /b 1
.venv\Scripts\python.exe -m tests.test_naming || exit /b 1
.venv\Scripts\python.exe -m tests.test_parser || exit /b 1
.venv\Scripts\python.exe -m unittest tests.test_page_fetch tests.test_aliases tests.test_enrichment -v || exit /b 1
echo PASS all tests
