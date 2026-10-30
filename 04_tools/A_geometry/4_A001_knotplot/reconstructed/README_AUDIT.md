# Read-only correction of the v0.1.0 KnotPlot census

The provided `metrics/*.csv` files report zero in their length columns for **all 50** objects. This is false: valid non-zero closed geometry is preserved in native `.kpf` and the corresponding ASCII exports. The KnotPlot CLI `data format "/N,/l"` is documented, but why the running scripts returned zero has not been established without console logs or rerunning KnotPlot. Do not silently overwrite those CSVs.

This audit reconstructs all lengths from **closed polygonal XYZ edges including the last-to-first edge, separately for every component**. It checks binary KPF (`LOCF`, network-endian float) against ASCII, count parity, finiteness, and expected gcd(p,q) component count for constructed torus links.

Native coordinates are in original KnotPlot units, **not SI**, and the torus cases are `torus p q` procedural constructs using KnotPlot's current settings, not immutable catalogue loads. No relaxation or sampling has been performed. The column `N_for_ds_1p2_reference_only` is a scenario diagnostic, not a prescription; the original geometry must remain intact.

## Certification limits

* Geometry: parsable and cross-format equivalent within `5e-5` coordinate units.
* Source identity: pending KnotPlot stdout/source catalogue hashes.
* Torus dynamics and topology: NOT validated by the gcd component-count check alone.
* Biot–Savart/finite-core dynamical resolution: NOT qualified by constant bead spacing.

## How to run

`py -3 reconstruct_census_v011.py falsifier_census_v0.1.0_output.zip OUTDIR`

Do not modify the original ZIP. Re-test the *KnotPlot* CSV writer in a new run by moving `length` to just before the `data` command and checking whether the zero value persists. Until it is understood, **use native-coordinate calculations as the primary audit**, not the `data /l` field.
