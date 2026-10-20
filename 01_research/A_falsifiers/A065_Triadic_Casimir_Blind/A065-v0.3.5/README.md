# A065-v0.3.5 -- Direct high-resolution trefoil convergence (to 4800 points)

Incremental version of v0.3.4. **No original D01/D02/D03 seal modifications.**
Previously failing G2, G11, and coarse-seed G13 retain their recorded negative evidence.

## Windows commands

```cmd
run_all.cmd VERIFY
run_all.cmd SELFTEST
set A065_THREADS=8
run_all.cmd HIGHRES
run_all.cmd ALL
```

`HIGHRES`: independent, immutable run with verified legacy D01/D02/D03 source seals and the new
A/B direct 600/1200/2400/4800 C++17 simulations at preregistered eps=.06,.12,.24; JSON, TeX, PDF, sealed exports.
It does not rerun the expensive v0.3.2 and v0.3.4 pilots; `ALL` runs those plus the canonical framework.
`ALL`: additionally runs official frozen SST framework v1.0.7 and the new G15-G18 scientific gate results.

C++17 compiler **g++** needed for high-resolution runs (`set CXX=g++`); OpenMP is auto-used if supported,
otherwise serial C++17. No GPU backend is claimed. Python runs the orchestration and N150 native parity
controls; N4800 dynamics is native C++ only. `A065_THREADS` integer 1-64; 4 by default.
On Linux: `./run_all.sh HIGHRES` and `./run_all.sh ALL`.

Always inspect `exports/<RUN_ID>/*_HIGHRES_V035_RESULT.json`, `*_FALSIFIER_REPORT.pdf`, and
`*_FRAMEWORK_FALSIFIER_REPORT.pdf` (the latter requires installed frozen v1.0.7).
Read `docs/HIGHRES_V035_CONTRACT.md` for blind thresholds, separate core scans and evidence limits.
All coordinates are dimensionless and historical analytical seeds; this does not certify Euler, Casimir or gravity.