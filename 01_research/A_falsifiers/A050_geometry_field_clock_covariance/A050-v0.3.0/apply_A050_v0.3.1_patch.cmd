@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "TARGET=%~1"
if not defined TARGET set "TARGET=%CD%"
if not exist "%TARGET%\project.json" (
  echo ERROR: pass the copied A050-v0.3.1 directory as argument, or place this script there.
  exit /b 2
)
pushd "%TARGET%"
git apply --check "%~dp0A050-v0.3.1.patch" || (popd & exit /b 1)
git apply "%~dp0A050-v0.3.1.patch" || (popd & exit /b 1)
popd
echo A050-v0.3.1 patch applied successfully.
endlocal
