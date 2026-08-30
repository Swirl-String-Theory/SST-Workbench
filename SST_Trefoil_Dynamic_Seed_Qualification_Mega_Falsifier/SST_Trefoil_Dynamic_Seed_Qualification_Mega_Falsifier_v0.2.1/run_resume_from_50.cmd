@echo off
setlocal
echo ============================================================
echo SST Trefoil Dynamic Seed Qualification Mega Falsifier v0.2.0
echo run_resume_from_50.cmd is intentionally disabled.
echo.
echo v0.2.0 changes S32 temporal certification, S35 champion semantics,
echo S37 mesh-gauge certification, and S40 long-run dynamics/eligibility.
echo Reusing a v0.1.x S40 result directly at S50 would bypass those gates.
echo.
echo To reuse a compatible v0.2.0 tree that already completed S10-S30, use:
echo   run_resume_from_32.cmd ^<output-dir^> ^<config.json^>
echo ============================================================
exit /b 2
