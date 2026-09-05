# v5 merge audit for uploaded v6 branch

This package is based on the user-supplied `sstcore_chiE_local_v6.zip` branch and preserves its additional v6 diagnostic scripts:

- `simulate_epsilon_sweep.py`
- `simulate_mass_mode_comparison.py`
- `simulate_trefoil_thickness_audit.py`
- `NEXT_TESTS.md`

The v5 mass-energy mode functionality is present and retained:

- Python `EnergyMassMode`
- Python `HornTorusParams.mass_mode`
- Python result fields `Xi_renormalization`, `Xi_mass`, `chi_renormalization`, `chi_E_hollow_total`, selected `chi_E`
- C++ `enum class EnergyMassMode`
- C++/pybind11 `HornTorusParams.mass_mode`
- C++/pybind11 selected-mass `chi_E` and renormalization outputs
- CLI `--mass-mode` support in the horn-torus, epsilon-sweep, and mass-mode comparison runners

Additional non-destructive merge addition:

- `run_chiE_bulk_matrix.py` for high-quality bulk option scans across lambda, epsilon, quadrature resolution, kernel, core constant, and mass mode.

No existing user-supplied v6 diagnostic files were removed.

## Export preservation

The generated exports from the uploaded v6 zip are preserved verbatim under:

```text
exports_uploaded_v6_preserved/
```

The active `exports/` folder may contain smoke-test outputs generated during merge validation.
