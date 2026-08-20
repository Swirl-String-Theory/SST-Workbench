# SST Threaded-Hole Substrate v0.2.0 — post-seal reveal

Seal verification: **PASS**.

## Self-confinement
- Carrier-clustered verdict: **INDETERMINATE** — active carriers 0, null carriers 1, p_active=1.

## Pressure law
- Central pressure: **INDETERMINATE_PRESSURE_DEFICIT** — favorable carriers 1/1, carrier-level p=0.5, median carrier Δp=-0.0359905.
- Even quadratic pressure law: **INDETERMINATE_PRESSURE_LAW** — B<0 carriers 0/1, median B=0.213221.

## Far-field gravity gate
- Free exponent: **INDETERMINATE_FREE_EXPONENT** — median carrier ν=2.35, carriers closer to ν=1 than ν=2: 0/1, p=1.
- Convergence: **NEEDS_OR_FAILS_FAR_FIELD_CONVERGENCE** — 0/0 carrier medians have ν-span <= 0.25.
- Combined: **GRAVITY_CLOSURE_NOT_SUPPORTED**.

## Stability islands
- 1 carriers have a reported best scanned full-horizon condition. These are **discovery only** and require a fresh confirmation campaign.

## Triple gear
- Phase-lock proxy available for 36 conditions; active score lower in 0. No mechanical ratio entered blind scoring.

Truncated/contact-stopped trajectories never enter normal AUC/RPO/Floquet pair scoring in v0.2.0.
