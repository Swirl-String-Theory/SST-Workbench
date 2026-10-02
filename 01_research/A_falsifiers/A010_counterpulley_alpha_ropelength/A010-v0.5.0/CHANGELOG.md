# CHANGELOG

## v0.5.0 -- Newton--Krylov Multiple-Shooting RPO Search

### Added

- `sst_counterpulley/rpo_solver.py`;
- matrix-free finite-difference Jacobian-vector products;
- restarted GMRES implementation with no SciPy dependency;
- multiple-shooting node corrections in a transverse Fourier/Kelvin basis;
- line-search merit that includes full-state segment defects;
- `run_newton_krylov.py` / `run_newton_krylov.cmd`;
- H0--H18 protocol;
- explicit longitudinal `Delta s_+-` gauge test;
- higher-resolution RPO confirmation gate before monodromy;
- full native and quick reference campaigns.

### Changed

- alpha unblinding gate moved from H14 to **H18**;
- `run_true_floquet.py` now runs Newton--Krylov RPO refinement before permitting monodromy;
- benchmark module remains unimported whenever H18 is closed;
- projected Newton convergence is no longer sufficient: full Cartesian recurrence is mandatory.

### Scientific conclusion

- Newton--Krylov improves the full shooting defect by about 9.4% in the full reference campaign;
- best full recurrence improves to `0.3463310365 D` but remains far outside the `0.05 D` RPO gate;
- endpoint-vectorfield mismatch remains `0.7562101428`;
- pure closed-filament longitudinal shift behaves as a refinement-dependent gauge artifact and is not admitted as a physical rescue parameter;
- no true Floquet monodromy or alpha comparison is scientifically permitted in the reference campaign.
