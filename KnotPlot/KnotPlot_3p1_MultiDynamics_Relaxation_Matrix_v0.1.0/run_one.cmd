@echo off
setlocal EnableExtensions
set "KP_SHORTCUT=C:\workspace\solo\_projects\SST-Workbench\KnotPlot\KnotPlot.lnk"
set "MATRIX_DIR=C:\workspace\solo\_projects\SST-Workbench\KnotPlot\KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0"

if "%~1"=="" (
  echo Usage: run_one.cmd ^<script.kpc^>
  echo Example: run_one.cmd 10_force_ablation_matrix.kpc
  exit /b 2
)
set "SCRIPT=%MATRIX_DIR%\%~1"
set "LOG=%MATRIX_DIR%\%~n1_console.log"
if not exist "%SCRIPT%" (
  echo ERROR: Script not found:
  echo   %SCRIPT%
  exit /b 1
)

for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%KP_SHORTCUT%'); [Console]::Write($s.TargetPath)"`) do set "KP_EXE=%%I"
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%KP_SHORTCUT%'); [Console]::Write($s.WorkingDirectory)"`) do set "KP_WORKDIR=%%I"
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%KP_SHORTCUT%'); [Console]::Write($s.Arguments)"`) do set "KP_ARGS=%%I"
if not defined KP_EXE exit /b 1
if not defined KP_WORKDIR set "KP_WORKDIR=C:\workspace\solo\_projects\SST-Workbench\KnotPlot"

pushd "%KP_WORKDIR%" || exit /b 1
"%KP_EXE%" %KP_ARGS% -nog ^< "%SCRIPT%" ^> "%LOG%" 2^>^&1
set "RC=%ERRORLEVEL%"
popd

echo Finished with exit code %RC%.
echo Log: %LOG%
exit /b %RC%
