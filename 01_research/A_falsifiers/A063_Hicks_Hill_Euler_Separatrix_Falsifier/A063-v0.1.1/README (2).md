# A063 Hicks/Hill Analytical Integration v0.1.1

**Status:** completed standalone analytical qualification release; NOT canonical v1.0.7-certified. Original A063 v0.1.0 and all historical falsifiers remain unchanged.

## Install

Copy the folders `01_research/` and `04_tools/` into the canonical `C:\workspace\projects\SST-Workbench` root. The former installs the new `A063-v0.1.1` alongside v0.1.0, the latter keeps the independent, non-mutating PDF report generator. This ZIP is a Workbench *overlay*, not an in-place modification of the canonical falsifier framework.

From `01_research\A_falsifiers\A063_Hicks_Hill_Euler_Separatrix_Falsifier\A063-v0.1.1`:

```bat
py -3 -m pip install -r requirements.txt
run_all.cmd SELFTEST
run_all.cmd FULL
```

Without `pdflatex`, the release will use the existing external gate-ledger PDF report as a fallback (with explicit downgrade recorded).

## Results in the included completed Linux reference run

- 13 gates: 10 PASS, 3 UNRESOLVED, 0 FAIL
- 12 Python tests PASS, including end-to-end run and JSON linkage
- New independent H7A: sampled winding 3/4, 4-poloidal-cycle 3D closure, candidate T(3,4) streamline, NOT certified finite-core knot
- H7/H7B: topological certification, trefoil global accessibility, finite-core tube stability UNRESOLVED
- H8: official v1.0.7/native C++ FP64 certification UNRESOLVED
- H6: 121-latitude, 3-offset interface convergence in 3 fields
- H9/H10: A046 and A057 analytic reference observables only

The enriched scientific report and ordinary external report are in
`01_research/A_falsifiers/A063_Hicks_Hill_Euler_Separatrix_Falsifier/A063-v0.1.1_external_reports/`.

`PARENT_PROVENANCE.json` gives SHA-256 links to the actual A063 v0.1.0 archive and five user-supplied historical result JSONs, without reclassifying them as evidence for v0.1.1.

The older falsifier framework versions can stay intact. This new release uses the external report generator; it is not an SST_Falsifier_Framework_v1.0.7 instance.
