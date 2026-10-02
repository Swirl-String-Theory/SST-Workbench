# SSTcore chiE local v7 merge audit

This package uses the user-uploaded `sstcore_chiE_local_v7.zip` as the base.
The merge is non-destructive: existing v7 source files from the uploaded package were kept as authority, including the solid-core files.

## Added from the prior merged branch

- `run_chiE_bulk_matrix.py` — bulk matrix runner for lambda/epsilon/kernel/mass-mode/quadrature sweeps.
- `V5_MERGE_AUDIT.md` — audit of the mass-mode / v5 merge.
- `USER_V6_EXPORTS_AUDIT.md` — audit for the preserved user v6 exports.
- `exports_uploaded_v6_preserved/` — user-supplied v6 export reference set.
- `exports_previous_preserved_before_user_v6/` — earlier preserved export reference set.
- `exports_previous_merged_active_reference/` — active exports from the prior merged branch, kept for comparison.

## Preserved from uploaded v7 base

- `simulate_solid_core_constant_density.py`
- `sst_solid_core_chiE.py`
- `test_solid_core_constant_density.py`
- existing horn-torus, epsilon sweep, mass-mode comparison, trefoil closure, and thickness audit scripts.

## Naming

The resulting artifact is intentionally still named `sstcore_chiE_local_v7.zip`, per request. It is a merged v7 line, not a v8 bump.
