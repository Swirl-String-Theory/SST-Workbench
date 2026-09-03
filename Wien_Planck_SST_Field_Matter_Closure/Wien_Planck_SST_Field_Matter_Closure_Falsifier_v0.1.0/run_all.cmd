@echo off
setlocal
call run_provenance.cmd || exit /b 1
call run_action_demo.cmd || exit /b 1
call run_action_negative_control.cmd || exit /b 1
call run_closure_demo.cmd || exit /b 1
echo.
echo ============================================================
echo Wien-Planck SST v0.1.0 complete
echo See outputs\
echo ============================================================
endlocal
