# Qualification/validation record — A063 v0.2.1

## Scope

Independent analytical/numerical **Python FP64 reference**, not independently reproduced mathematical proof or experimental campaign.

The parent baseline hash is checked, including its gate ledger and original source seal. The new instance produces its own local source manifest, run summary, gate ledger, and PDF. The new S gates are distinct from historical T gates.

## Registration and failure semantics

- Frozen registered level ratios: 0.9, 1.0, 1.1 relative to the rational-line `psi0` selected previously.
- Reference first-Beltrami root `lambda=4.4934094579...`, `a=rho=A=1`.
- One finite-difference normal-flux ladder: `(2e-4,1e-4,5e-5)*a`.
- Mesh levels: 96, 192, 384 meridional sample points, plus analytically exact azimuthal symmetry of the steady field. Only meridional evaluations are performed; azimuthal copies are **symmetry equivalents**, not separate raw evaluations.
- S6 FAIL means the specific `psi`-level construction has an unknotted center core. Other knotted tube constructions remain scientifically undecided.
- S7 FAIL means pitch shear on neighboring level surfaces; it is **not** a 3D Euler growth rate.
- S9, S10, S11 UNRESOLVED until independently qualified dynamics/certification exist.
- All scientific gates continue independently when previous gates FAIL.

## Automated validation

`python -m pytest tests -q` — 17 PASS (performed during package construction).

`python run_invariant.py --mode FULL` — 7 PASS / 2 FAIL / 3 UNRESOLVED (12 new gates).

The PDF was rendered and inspected across all pages. There is no native C++ backend claim. Framework v1.0.7 is deliberately not modified.
