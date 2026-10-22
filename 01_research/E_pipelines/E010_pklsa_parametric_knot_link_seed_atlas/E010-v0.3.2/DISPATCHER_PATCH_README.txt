A058-v0.3.7 -- Launcher Dispatch Hotfix (22 Oct 2026)

Issue:
    run_all.cmd QUALIFY_EXISTING ... was sent to bridge.py, whose modes predate v0.3.7.

Installation:
    Copy run_all.cmd and tools/native_measurement.py from this ZIP DIRECTLY into
    your existing A058-v0.3.2 project directory, replacing run_all.cmd.
    The ZIP has no enclosing directory so you can extract over the project root.
    Do not overwrite existing results, private data, or blind-protocol files.

Verify from the project root (CMD):
    findstr /C:"QUALIFY_EXISTING" run_all.cmd
    dir tools\native_measurement.py

Then:
    run_all.cmd QUALIFY_EXISTING --source ".\A058_probes3.zip" --out ".\A058_v037_qual3"

Exitcode 2 denotes a complete but scientifically FAILED measurement qualification.
Original A058 measurements and the 271 registered conditions are not changed.

Validated on Linux: actual project test suite, 66/66 PASS; dispatch routing
statically checked. Windows command interpreter not available in this environment.
