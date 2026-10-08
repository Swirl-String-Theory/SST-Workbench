@echo off
setlocal
echo A056 is intentionally manual-phase. Do NOT auto-run all science phases.
echo Run run_00_verify.cmd, then run_01... through run_09 one at a time.
echo Finally use run_10_finalize_blind.cmd, run_11_reveal_if_allowed.cmd, run_12_post_reveal.cmd.
exit /b 0
