@echo off
setlocal enabledelayedexpansion

if "%PYTHON%"=="" set PYTHON=python

REM Extended convergence scan.
REM Corrected IDs: 3_1=3:1:1, 5_2=5:1:2, 6_1=6:1:1.

for %%K in (3:1:1 5:1:2 6:1:1) do (
    set KID=%%K
    set SAFE=!KID::=_!
    for %%N in (2048 4096 8192) do (
        for %%S in (5 9 15) do (
            set OUT=results_ext\02_ideal_!SAFE!_N%%N_S%%S
            %PYTHON% scripts\sst_ffs_02_filament_projection_ideal.py --curve ideal --ideal-file data\ideal.txt --ideal-id !KID! --natural-scale --n %%N --smooth-width %%S --ells 1 2 4 8 13 21 28 34 55 89 --outdir !OUT!
            if errorlevel 1 exit /b 1
            %PYTHON% scripts\sst_ffs_03_attachment_threshold_scan.py --summary-csv !OUT!\sst_ffs_02_summary.csv --spectrum-csv !OUT!\sst_ffs_02_spectrum.csv --ells 1 2 4 8 13 21 28 34 55 89 --outdir results_ext\03_threshold_!SAFE!_N%%N_S%%S
            if errorlevel 1 exit /b 1
        )
    )
)

echo Done. Check results_ext.
