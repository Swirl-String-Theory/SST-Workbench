# A068 v0.4.2 — external A004 historical geometry import

**Versioned patch, new falsifier instance.** Keeps A068 v0.4.1 frozen/unmodified.

## One command (Windows)

Extract the zip and run `SETUP_A068.cmd` (or `py -3 setup_A068.py --workbench-root C:\workspace\projects\SST-Workbench`).

1. Verify every file against the distribution manifest, then the science contracts.
2. Install `A004_LIBRARY_PAYLOAD` **only if** this exact canonical release is absent:
   `02_libraries/A_knot_libraries/A004_historical_trefoil/SST_Historical_Trefoil_XYZ_v0.2.2/`.
   A004 is never merged into or overwritten. If the folder is partially installed,
   setup aborts. The older typo `A004_historical_trefoiul` is detected and must be
   resolved before setup.
3. Audit A004 manifest SHA-256 and all 40 XYZ files; validate mirror and fixed-origin reversal.
4. Generate a **new** `A068-v0.4.2` through the original framework `v1.0.8` generator;
   install the science overlay with the A004 adapter; run regressions; perform FREEZE
   on Windows, creating fresh nonces/private commitments for v0.4.2.
5. Run `run_all.cmd BASIC`, `FULL`, `CERTIFY` from new A068-v0.4.2 folder.

## Import API (in the A068 instance)

```python
from experiment.a004_adapter import load_seed
xyz = load_seed(model="B", chirality="orig", traversal="ccw",
                resolution=1200, version="0.2.2",
                workbench_root=r"C:\workspace\projects\SST-Workbench")
```

The library contains *geometry seeds*, not measured PKLSA velocity fields.
`N=600...9600` measures centerline sampling, **not** the Euler grid.
The native KnotPlot seed remains the independent primary A068 numerical-control input.
Historical A/B Euler pilots use external A004 XYZ files, not A068 copies.
Any missing source or changed hash => `G1 FAIL` and no physical gates/reveal.
`G3` remains `UNRESOLVED` until an actual material vortex, RPO, Floquet
and physical-provider conditions are qualified.

Never change the A004 release after A068 v0.4.2 FREEZE. A new A004 generator
release or any science-contract change needs a new A068 falsifier version.

## Verification without mutation

`py -3 setup_A068.py --verify-only --workbench-root C:\workspace\projects\SST-Workbench`

## Output

- `A004_IMPORT_AUDIT.json` — external library identity and 40 SHA-256 hashes
- `HISTORICAL_2015_EULER_MODEL_DIAGNOSTICS.json` — A/B geometry pilots
- Standard framework PDF, BLIND-ZIP, gate ledger and SHA-256 output manifest

No physical PKLSA clock, C++/SYCL parity, SI scale or physical source-independence
is asserted by this patch.
