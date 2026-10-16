# A058 v0.1.4 Validation Record

Status: **RECOVERY_ANALYSIS_READY**

## Defects repaired from v0.1.3

1. Framework-v1.0.6 gate collision: v0.1.3 repurposed G6 for relaxation plateau although the framework reserves/remaps G6 for GPU screening. v0.1.4 restores G4/G5/G6/G7 to framework semantics and evaluates A058 convergence at G8.
2. All 150 KnotPlot `metrics.csv` files in the completed v0.1.3 pilot were zero bytes. v0.1.4 treats them as missing and uses the complete ASCII coordinate acquisition.
3. v0.1.3 source-contract paths resolved incorrectly against Workbench root. v0.1.4 uses full Workbench-relative instance paths.
4. v0.1.4 imports v0.1.3 public campaign artifacts read-only; no KnotPlot rerun is required.

## Validation against supplied v0.1.3 outputs

- 150/150 conditions in runlog.
- 0 non-zero KnotPlot exits.
- 900/900 expected coordinate checkpoint files present and parseable.
- 150/150 metrics CSV files present but zero bytes.
- dstep final outputs byte-identical to baseline across all tested topology IDs.
- dstep max D_shape: 4.451870114035978e-15.
- force-ablation median D_shape: 0.0571020174955731.
- plateau pass fraction: 0.6 (required 0.8).
- resolution median D_shape: 0.017357223181645266 (threshold 0.01).
- anonymous same-topology generator-pair D_shape: 0.571742578232028 (threshold 0.01).

## Framework contract checks

Using the exact v1.0.6 validator modules:
- science contract: PASS (no errors)
- source contract: PASS (no errors)
- gate plan: PASS (no errors)
- report section contract: PASS (no errors)
- blind-tree scan: PASS (0 forbidden-term hits)
- nonced blind/reveal commitments: PASS
- FREEZE simulation: PASS
- frozen-protocol verification: PASS

## Unit tests

Six instance tests pass when run against a v1.0.6-compatible framework root.

## Scientific boundary

This release is a recovery/reanalysis of already acquired v0.1.3 simulation data. It is not an independent confirmation campaign. Existing v0.1.3 acquisition bytes remain immutable provenance.
