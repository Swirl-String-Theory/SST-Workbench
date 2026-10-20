# A065-v0.3.6 -- Direct high-resolution trefoil convergence (to 4800 points)

Incremental version of v0.3.4. **No original D01/D02/D03 seal modifications.**
Previously failing G2, G11, and coarse-seed G13 retain their recorded negative evidence.

## Windows commands

```cmd
run_all.cmd VERIFY
run_all.cmd SELFTEST
set A065_THREADS=4
run_all.cmd GENERATE
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

## v0.3.6: direct Python generation inside the falsifier

`run_all.cmd GENERATE` generates BOTH 2015 analytic trefoils directly at N=600,1200,2400,4800,
using `triadic/parametric_generator_v036.py` (Python stdlib; original historical
`data/HISTORICAL_2015/regenerate.py` remains byte-identical and hash-pinned).
Each generated coordinate array is independently checked against the immutable
v0.3.5 XYZ sources (difference <1e-7). New generated XYZ outputs live only in
`outputs/GENERATED_V036_XYZ/` inside the unique run snapshot, not in original `data`.

`epsilon=0.06` is **dimensionless smoothing length** in the regularized
midpoint-segment velocity denominator `(r*r+epsilon*epsilon)^(3/2)`, not a
measurement or derivation of SST physical `r_c`. Gamma=1, T=.04, steps=8.
N is varied at FIXED epsilon; segment length / epsilon is tabulated explicitly.
New registered official gates: **G19 geometry identity**, **G20 geometry-to-epsilon
diagnostic** (at N4800 ds/epsilon <0.25), **G21 native fixed-epsilon convergence**
(1200/2400 and 2400/4800 <1% on both analytic curves). Coarse 600/1200
failures remain visible. G2/G11/G13 FAIL and physical G3 UNRESOLVED are never
promoted or rewritten.

`GENERATE` outputs `GENERATED_V036_RESULT.json`, regenerated XYZ files and a PDF.
`ALL` also calls this new module and registers G19-G21 through the unmodified
external framework v1.0.7. Set `A065_THREADS=8` (or 16) for native C++ OpenMP.
