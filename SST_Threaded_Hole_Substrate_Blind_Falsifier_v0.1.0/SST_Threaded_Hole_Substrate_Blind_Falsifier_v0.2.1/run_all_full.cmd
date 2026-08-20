@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_00_install.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
for %%C in (extended pressure_law far_field confirmatory_stability thread_focusing similarity triple_gear) do (
  call run_%%C_prepare.cmd || exit /b 1
  call run_%%C_blind.cmd || exit /b 1
  call run_%%C_reveal.cmd || exit /b 1
)
echo [SST-TH v0.2.1] full core complete.
echo Optional long scans: run_all_fixed_per_thread.cmd and run_all_stability_islands.cmd
exit /b 0
