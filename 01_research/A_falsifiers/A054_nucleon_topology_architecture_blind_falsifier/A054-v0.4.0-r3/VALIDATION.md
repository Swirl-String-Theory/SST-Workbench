# A054 v0.4.0-r3 validation

**Framework target:** SST Falsifier Framework **v1.0.4 CANONICAL_FROZEN**  
**Status:** **INSTANCE MAINTENANCE VALIDATED / PHYSICS UNCHANGED**

## r3 checks
- scientific contracts, source cohorts, mechanism arms, gain grid, and v0.2 hard gates: **unchanged from r2**;
- public forbidden-term scan of the packaged instance tree: **PASS, 0 hits**;
- virtual environment moved outside the blinded instance root, preventing third-party `site-packages` from entering framework blind scans;
- legacy local `.venv` is removed during setup migration;
- corrected `report/FALSIFIER_REPORT.tex` compiled successfully with `latexmk`/`pdflatex` against the r2 generated `AUTO_SCIENCE_CONTRACT.tex` and `AUTO_RESULTS.tex`;
- source tests in the current container: **4 passed, 2 skipped** because the maintenance validation did not rebuild the native extension;
- r2 native C++ source is byte-identical in r3 and had already passed ELASTIC/CORE native-reference parity and OpenMP validation before this maintenance change.

## User r2 run used to diagnose r3
The Windows r2 run successfully built the CPython 3.14 native wheel, installed Framework v1.0.4, passed the framework selftests, froze protocol SHA-256 `103113f12b5c652adea2f4f52ae0b0a594a4c94ef10b1d322cd6a187ff61fda9`, and completed the BASIC scientific pipeline. It failed only during report rendering and blind packaging.

The r2 BASIC blind scientific result was `NO_REGISTERED_MECHANISM_RECOVERS_DISCOVERY`; this maintenance release does not modify or reinterpret that result.

## r3 frozen protocol
`b4f667c3af0a262459da65768e65bfa2acc4dbe04374751ebfc128dc68b464b9`
