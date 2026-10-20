# A068 PKLSA Intrinsic Phase Clock v0.4.0

Official SST Falsifier Framework **v1.0.8** instance.

Already configured: `science_contract.json`, `source_contract.json`,
`gate_plan.json`, `blind_policy.json`, `report/FALSIFIER_REPORT.tex`,
`experiment/pipeline.py` and `experiment/{material,rpo,floquet,dynamics}.py`.

The A064-derived `experiment/euler3d.py` is byte-for-byte unchanged;
its sources are versioned and hash-verified. No `REPLACE_BEFORE_FREEZE` tokens.

A single material mesh advected with RK4 is a material **surface**; check
vorticity tangency and material volume for a vortex **tube**. The full-field
relative orbit search is a symmetry-aware candidate scan, not a nonlinear
shooting certification. Tangent linearization is finite-difference checked.
Only after accepted material vortex + certified RPO is Floquet Ritz considered;
its eigenpair residual and mesh/subspace convergence are still required.

Existing historical geometry is uncalibrated and *unblinded*; no native
independent physical PKLSA provider exists. Physical G3 remains UNRESOLVED.
No changes to private secrets, no reveal forcing. For changes after FREEZE,
create a NEW version rather than modifying this one.

After setup, run from new A068-v0.4.0 instance:
`run_all.cmd BASIC`, `run_all.cmd FULL`, `run_all.cmd CERTIFY`.
Outputs: `EULER_DYNAMICS_RESULTS.json`, `EULER_3D_FIELDS_MODEL_ONLY.npz`,
`MATERIAL_TUBE_DIAGNOSTICS.json`, `RPO_AND_FLOQUET_DIAGNOSTICS.json`, BLIND
ZIPs, gate-ledger, and automatic LaTeX/PDF report.
