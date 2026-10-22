# A058 change log

## v0.3.7 (22 October 2026): Native Measurement Qualification

- Added read-only requalification of user-owned A058_probes3/probes4 source ZIP/folders: native scalar CSV cross-check against independent XYZ and console, `/I` iteration value, `safe` markers, `KP-alex.exe` runtime failure, and missing `dstep` getter.
- Introduced new controlled four-case native diagnostic (dstep 1/4 × `data open` BEFORE/AFTER length/rog) to isolate native `data` zero-value defect. Geometry, working directory, force exclusions, and matched solver budget held fixed.
- Added Windows `.lnk` support by reusing the v0.3.6 resolver (including literal `%SST-Workbench%` expansion). All test I/O uses absolute A058 paths; no global `cwd` hack.
- Added fail-closed non-overwrite preflight, SHA-256 input hashes, raw PRIVATE stdout retention, console/CSV/XYZ readback gates; never silently converts missing values into zeros.
- `alex -1` removed **only from the NEW isolated measurement diagnostic**. Prior historical experiments remain immutable.
- Existing A058 271 blind-condition protocol, source pin, cloned v0.2.9 engine, gate ledgers, original native results: unchanged.
- Local regression 66/66 PASS with authentic 2025 distribution; new 2026 Windows native run NOT_PERFORMED.
