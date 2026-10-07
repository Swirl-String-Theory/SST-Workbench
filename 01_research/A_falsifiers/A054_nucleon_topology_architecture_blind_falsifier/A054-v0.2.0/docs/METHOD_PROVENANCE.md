# Method provenance — A054 v0.2.0

A054-v0.2.0 is a new three-component certification consumer. It does not copy pass/fail outcomes from prior work; it reuses methodological constraints from two already-developed SST numerical lines.

## A021 trefoil coupled-mode / RPO-Floquet line

Reused method ideas:

- finite-core Biot–Savart dynamics without hand-written restoring/contact forces;
- quotienting rigid translation, rigid rotation, and tangential marker motion;
- finite-difference Jacobians at multiple perturbation amplitudes;
- breathing/torsion/Kelvin-like perturbation families;
- nonlinear ringdown as a separate gate;
- RPO recurrence must contain a genuine excursion and return;
- Floquet/monodromy is interpreted only after accepted recurrence.

A054 does **not** import the trefoil result itself. Thresholds explicitly inherited from the A021 BASIC method are identified in `configs/cert_*.json`.

## C006 Kelvin/Floquet Workbench v0.3.0

Reused integrity rules:

- frozen local Kelvin spectra are distinct from true relative Floquet spectra;
- `No accepted RPO -> no true Floquet monodromy`;
- one neutral phase multiplier nearest 1 is removed only after a genuine relative-periodic return has been established;
- resolution persistence is checked before interpreting spectral branches.

A054 generalizes the perturbation basis from one trefoil to three interacting closed components; it does not claim that a projected finite-dimensional spectrum proves full Euler stability.

## v0.1.1 evidence boundary

The frozen v0.1.1 summaries are stored under `data/v011_evidence_freeze/`. They motivate which architectures/compositions are adversarially certified, but **their measured effect sizes are not used to set any v0.2.0 hard threshold**.
