# A064 v0.2.2 — Validation, test and qualification ledger

- Three distinct geometries of L6n1 / three-Hopf class; **not** a Borromean test.
- Source-native XYZ from Google Drive: `link_6.3.3.txt`, `torus_3.3.txt`; input SHA256 stored inside source provenance.
- Parameteric analytic Triple Gear proxy uses Schleimer–Segerman centreline placement. NOT full extracted physical STL, no gear teeth or mechanical contact.
- All three component Alexander determinant screens: 1, 1, 1; all absolute pairwise Gauss linking ~1. Three independent fixed projection views per component.
- 13 time-varying solver frames per completed case; Euler energy/divergence diagnostics are computed and preserved, source NPZ SHA256 verified.
- 8 completed model runs: all 3 cases on N=24 and N=32, plus L6n1/T33 on N=48.
- Triple Gear proxy N=48: **NOT_COMPLETED** due execution timeout. This is not a numerical fail of the physical model; it is a missing convergence rung.
- Discovery seal: SHA-256 over canonical selected discovery JSON before any transport output; NOT an official blind protocol.
- 10 passing selftests after numerical production on N=24.
- Data does not establish material vortex tubes, topologically robust invariant manifolds, mechanically entrained phase modes, physical PKLSA fluid, or SST.
- Official frozen SST framework 1.0.7 FREEZE/CERTIFY: NOT EXECUTED.
- Scientific gates: TRUE_DYNAMIC_SEPARATRIX UNRESOLVED; TRANSPORT_CONVERGENCE UNRESOLVED; MECHANICAL_TRIPLE_GEAR UNMODELED; E011_PROVENANCE UNRESOLVED.
- Results are immutable *per-run folders*, rebuild requires explicit `--force` if hashes or parameters differ. `REPORT` sees incomplete runs as NOT_COMPLETED.
