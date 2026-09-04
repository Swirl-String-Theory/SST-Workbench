@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo SST Math Lab v0.2.0 - core smoke test
echo ============================================================
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js was not found.
  echo Use the in-browser "Run self-test" button instead.
  pause
  exit /b 1
)
node "%~dp0tests\core_smoke_node.js"
if errorlevel 1 (
  echo.
  echo SELF-TEST FAILED.
  pause
  exit /b 1
)
echo.
echo SELF-TEST PASSED.
pause
exit /b 0
