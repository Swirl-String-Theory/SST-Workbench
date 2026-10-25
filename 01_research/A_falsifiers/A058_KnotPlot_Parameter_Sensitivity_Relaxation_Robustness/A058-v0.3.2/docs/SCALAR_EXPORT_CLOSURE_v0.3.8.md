# Scalar export closure — v0.3.8

## Scope and falsifiable gates

The historical A058-v0.3.7 study isolates an **ordering dependency**: with the same seed and 32 steps, `data open` before `length` and `rog` outputs valid CSV scalars for dstep 1 and 4, whereas opening afterward outputs zeros. The internal invalidation mechanism (`data open` vs `data format` vs `data header`) remains unidentified.

## New native six-case experiment

Each dstep setting (1 and 4) is crossed with independent solver horizons (32, 128, 512 iterations). Each KnotPlot process starts from the identical original distribution `basic/3.1` seed; no data or script is overwritten. Native session policy: `reset all`, `collision fast`, explicit off flags (`velforce`, `tanf`, `grav`, `therm`), start readback, start `safe`, run `go N`, final readback, final `safe`, then initialize `data open/format/header`, execute `length`, `rog`, `data`, `data close`, and export ASCII coordinates.

Controls are *one row per process* rather than multiple `data` writes in one process to avoid assuming undocumented multi-checkpoint caching semantics. This increases run count but permits unambiguous per-horizon readback and output correspondence.

### Native qualification gates

| Gate | Criteria | Fail when |
|---|---|---|
| Process | exit code 0, no fatal diagnostic | nonzero, timeout, fatal string |
| Native state | dstep pre/post equals registered setting; iteration pre=0/post=N; force flags off | missing/readback mismatch |
| Endpoint status | explicit positive safe start and final | missing or not safe |
| Scalar row | exactly one row, 4 required numeric columns, finite values | missing, nonfinite, extra row |
| Geometry | parsable finite closed XYZ and positive length/Rg | invalid/missing points |
| Correspondence | Nbeads/iteration exact; length and Rg within frozen v0.3.7 tolerance `max(2e-5,1e-6*abs(XYZ))` | mismatch including silent zero |
| Provenance | design hashes, seed, script; no evidence overwrite | hash mismatch, prior run |

Only a complete six-case gate PASS produces `native_scalar_closure: PASS`. The output also records each finite-time geometric change but makes no physical-stability claim. There is no Alexander/topology certification in this module.

### Historic evidence semantics

The four existing v0.3.7 outputs remain immutable: two **numerical PASS** controls and two **expected numerical FAIL** controls. Their **method experiment** can pass as a positive/negative-control pattern, without altering their individual scalar statuses.

### Outputs

- `CLOSURE_DESIGN.json`: immutable run registration and seed/source SHA-256.
- `dstep_<d>_go_<N>/probe.kpc`: original portable script, independent KPF seed.
- `.../probe.native.kpc`: absolute input/output paths resolved from the requested output directory.
- `.../NATIVE_STDOUT_PRIVATE.log`: private raw native output.
- `.../A058_native_metrics.csv`: one native CSV record.
- `.../A058_final.txt`: corresponding native XYZ snapshot.
- `qualification/CLOSURE_AUDIT.json`, `CLOSURE_MATRIX.csv`, `CLOSURE_REPORT.md`: numerical gate results.

Private stdout is never copied into the bundled historical summary. KnotPlot GUI `.lnk` is not modified; its `Start in` directory is honored. No call to `alex -1`, `KP-alex.exe`, or the original 271-condition runner is made.
