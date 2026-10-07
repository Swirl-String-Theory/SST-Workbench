# A056 v0.2.3 preregistration

This release preserves the v0.2.2 scientific thresholds while moving the experiment onto SST Falsifier Framework v1.0.4 CANONICAL_FROZEN.

## Primary nulls

1. Sine-Gordon is not required: it does not beat Wave/Klein-Gordon/Duffing on discovery and held-out confirmation.
2. Fractional memory is not required: Mittag-Leffler does not beat exponential, stretched-exponential and bi-exponential alternatives.
3. Any confirmed preference fails numerical certification and/or eligible physical cross-source replication.

## Frozen splits and thresholds

Phase discovery uses the first 65% of temporal samples; the final 35% is held out. Ringdown uses 70/30. Sine-Gordon support requires positive fitted `a,b`, design condition number <= 1e8, discovery Delta-BIC >= 10, and held-out NRMSE ratio <= 0.95 (`basic`) or <= 0.93 (`full`).

Mittag-Leffler support requires Delta-BIC >= 10, the same profile-specific held-out ratio, and `0.48 < alpha < 0.97`, keeping the ordinary exponential boundary `alpha=1` outside the support region.

Numerical certification requires deterministic 2x coarsening stability and Python-FP64/C++-FP64 parity <= 1e-10. DD32/FP32x2 remains screening-only.

## Replication

Canonical framework evidence classes apply. Only `independent_source` and `experimental` rows can close physical cross-source replication. Synthetic controls and simulations are reported separately and cannot promote G7/G8 to a physical PASS.
