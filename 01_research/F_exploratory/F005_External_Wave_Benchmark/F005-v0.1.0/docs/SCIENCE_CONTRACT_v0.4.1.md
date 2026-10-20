# F005-v0.4.1 Science Contract (DEVELOPMENT)

## Locked inputs

- Original `source_lock()` function reused from v0.4.0, including source-hash and training-model audits from v0.3.0.
- ARX(2) coefficients from v0.3.0 are **frozen** (`A=1.9856661039519918`, `B=-0.9908696423084401`, `C=-1.118156917616826`).
- `dt=0.004 s`; anchors `0.004, 1.5, 2.8 s` and horizons `0.1, 0.5, 1, 2, 3 s` unchanged.
- Input acceleration is known for the full conditional horizon, but the model does not read future water-height values for recursion.
- Evaluation cohort: only 750 `STANDARD_VALIDATION` trajectories.
- No TEST/OOD output trajectories accessed; no source archives read or modified.

## P5b exact vs approximate operations

- Exact input duplicate search: all finite input traces hashed in their original floating-point bytes. Complete for exact duplicates; does not certify same physical family.
- Approximate normalized morphology: deterministic sampling across 3 fingerprint widths; capped at 15,000 scored candidate pairs by a predeclared stable ordering.
- Candidates may be omitted even if near-identical. Therefore `P5b` is REVIEW whether or not suspicious pairs are found.
- No source-provided family identities are available; no blind holdout certification.

## P6a metric

For time origin `n0`, seed observed values `eta[n0-1]`, `eta[n0]` and recursively simulate

`eta_pred[n+1] = A eta_pred[n] + B eta_pred[n-1] + C a[n] dt^2`.

Compute RMSE on the *fixed terminal sample* at each predefined horizon; compare with persistence and two-point linear extrapolation. The metrics **are terminal-horizon errors**, not average-trajectory errors or Euler model validation.

If approximate family review is unresolved, P6a is nevertheless permitted to execute, **strictly as DEVELOPMENT**. A successful prediction cannot promote P5b, P7 or P8.

## Falsifiable next step

Source-provided trajectory generator/group IDs and a group-disjoint split; independently derived tank sloshing modes; then blind out-of-sample Euler and PKLSA forecasts on unchanged input protocols.
