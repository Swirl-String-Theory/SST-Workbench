# CHANGELOG v0.1.6

## Adaptive KnotPlot catalogue-load strategy

v0.1.5 correctly located `basic\3.1`, but this KnotPlot Windows build still
reported `nothing loaded` when an absolute Windows path was passed to `load`.

v0.1.6 no longer assumes one load syntax. Before any campaign it probes:
1. shortcut CWD + `load 3.1`;
2. shortcut CWD + `path <basic>` + `load 3.1`;
3. `basic` as process CWD + `load 3.1`;
4. `basic` as process CWD + `load ./3.1`.

A strategy passes only when KnotPlot creates both a non-empty `.k` and coordinate
`.txt` probe with no hard load/save errors. The first proven strategy is frozen
for the complete discovery run and reused for catalog runs.

The probe explicitly deletes prior probe outputs before every attempt, preventing
stale files from causing a false PASS.
