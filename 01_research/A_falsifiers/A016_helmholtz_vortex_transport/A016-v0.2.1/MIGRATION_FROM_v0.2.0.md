# A016 migration analysis: v0.2.0 -> v0.2.1

## Problem found in v0.2.0

v0.2.0 correctly fused the Helmholtz population/field program with the original A016 H0-H4 branch, but its external geometry contract still pointed directly at `KnotPlot/knots/final`. That made one relaxed-centerline library the sole geometry provider even though PKLSA had become the Workbench geometry qualification/provenance layer.

This is a source-architecture defect, not a reason to retune any physical threshold.

## v0.2.1 correction

v0.2.1 consumes the E010/PKLSA v0.4.0 publication-ready geometry layer. The adapter verifies the release schema/version, topology qualification summaries, carrier descriptors, source paths, and raw source-file hashes. Carrier identities are retained only in the private reveal map.

The old KnotPlot/RidgeRunner route is not discarded: when present in PKLSA it remains one upstream source family among the qualified carrier population rather than being hard-coded as the entire A016 dataset.

## New X0 gate

X0 detects whether conclusions change with geometry provider. For each topology it groups upstream carriers by PKLSA `provider_group`. Multiple carriers from one provider are correlated and collapse to one vote. Generated/derived carriers are measured but never counted as independent closure evidence.

The frozen comparison set is `H2,H3,P3,P4,P5,P6`. Provider agreement must be at least 0.80 and at least two upstream provider groups must be represented. If no topology meets the provider minimum, X0 is `UNRESOLVED`, not PASS.

## Scientific continuity

No H0-H4 or P0-P6 equation/threshold is changed. v0.2.0 therefore remains a useful pre-PKLSA baseline, while v0.2.1 is the first release intended for atlas-level provider robustness.
