@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
set "N=%~1"
if not defined N set "N=8"
set "TSFILE=.sst_timestamp_archive_extra_shards.tmp"
".venv\Scripts\python.exe" tools\timestamp.py > "%TSFILE%" || exit /b 1
set /p TS=<"%TSFILE%"
del /q "%TSFILE%" >nul 2>&1
if not defined TS set "TS=manual"
set "ROOTOUT=outputs_archive_extra_extended_sharded_%TS%"
mkdir "%ROOTOUT%" >nul 2>&1
set /a LAST=N-1
echo [SST] EXTRA_EXTENDED archive in %N% deterministic shards -^> %ROOTOUT%
for /L %%I in (0,1,!LAST!) do (
  echo ============================================================
  echo [SST] Shard %%I / !LAST!
  ".venv\Scripts\python.exe" run_archive_campaign.py --config configs\archive_extra_extended.json --out-dir "%ROOTOUT%\shard_%%I" --backend auto --shard-count !N! --shard-index %%I
  if errorlevel 1 exit /b !errorlevel!
)
".venv\Scripts\python.exe" tools\merge_archive_shards.py "%ROOTOUT%" || exit /b 1
echo [SST] Merged summary: %ROOTOUT%\MERGED_ARCHIVE_SUMMARY.md
exit /b 0
