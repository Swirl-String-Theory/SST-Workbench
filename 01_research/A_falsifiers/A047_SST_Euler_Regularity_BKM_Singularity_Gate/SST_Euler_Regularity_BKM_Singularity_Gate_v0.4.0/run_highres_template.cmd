@echo off
echo WARNING: v040_highres_template reaches N=128 and can be very expensive.
call "%~dp0run_all.cmd" "%~1" config\v040_highres_template.json "%~2"
