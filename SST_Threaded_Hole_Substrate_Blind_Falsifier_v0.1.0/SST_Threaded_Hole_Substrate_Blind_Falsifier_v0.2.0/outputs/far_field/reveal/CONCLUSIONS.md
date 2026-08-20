# SST Threaded-Hole Substrate v0.2.0 — post-seal reveal

Seal verification: **PASS**.

## Self-confinement
- Carrier-clustered verdict: **INDETERMINATE** — active carriers 0, null carriers 0, p_active=1.

## Pressure law
- Central pressure: **SUPPORTS_THREAD_DENSITY_PRESSURE_DEFICIT** — favorable carriers 6/6, carrier-level p=0.015625, median carrier Δp=-0.123439.
- Even quadratic pressure law: **SUPPORTS_NEGATIVE_EVEN_QUADRATIC_THREAD_PRESSURE** — B<0 carriers 6/6, median B=-0.123439.

## Far-field gravity gate
- Free exponent: **INDETERMINATE_FREE_EXPONENT** — median carrier ν=2.1625, carriers closer to ν=1 than ν=2: 1/6, p=0.984375.
- Convergence: **NEEDS_OR_FAILS_FAR_FIELD_CONVERGENCE** — 0/6 carrier medians have ν-span <= 0.3.
- Combined: **PRESSURE_DEFICIT_SUPPORTED_FAR_FIELD_NOT_CLOSED**.

## Stability islands
- 0 carriers have a reported best scanned full-horizon condition. These are **discovery only** and require a fresh confirmation campaign.

## Triple gear
- Phase-lock proxy available for 0 conditions; active score lower in 0. No mechanical ratio entered blind scoring.

Truncated/contact-stopped trajectories never enter normal AUC/RPO/Floquet pair scoring in v0.2.0.
