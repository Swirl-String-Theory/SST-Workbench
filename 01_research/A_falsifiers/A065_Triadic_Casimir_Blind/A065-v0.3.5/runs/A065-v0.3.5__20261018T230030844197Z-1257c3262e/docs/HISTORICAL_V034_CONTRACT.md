# A065-v0.3.4 — historical parametric trefoil geometry and XYZ numerical control

Preregistration SHA256: `73545eaddc62a3f2eda0553610220812758dc628ad2aa0eb8d4e9177d36207e5`.

Two distinct seed families from historical notebook (2015), pages 32 and 66. Original uploaded XYZ N600/N1200 and exact byte hashes are carried under data/HISTORICAL_2015. **Not independent physical providers**, no valid SST SI scale and not dynamically PKLSA-relaxed.

For each seed, validate SHA256, closed periodic polygon, near-constant arc-length spacing, analytic curve length, and N600 vs N1200 phase alignment. No retuning or scaling across seeds.

Then integrate the same existing dimensionless regularized midpoint filament Biot-Savart ODE via C++17 RK4 (Python independently checks N150 trajectory). Use Gamma=1, epsilon=0.12, T=0.04, 8 RK4 steps. Spatial comparisons: N150 to N300, N300 to N600, N600 to N1200; independent geometric data N600/N1200 are not independent dynamic source families. Time refinement N300 (4, 8, 16 steps). Sensitivity epsilon=0.06 and 0.24 on N300 with unchanged Gamma,T. Accept spatial < 5%, temporal < 0.1%, parity RMS < 1e-10. Do **not** promote failed checks.

G12 = geometry integrity, G13 = reduced ODE numerical convergence, G14 = completed sensitivity scan; original G2 FAIL, G10 PASS, G11 independent Fremlin FAIL and G3 physical UNRESOLVED unchanged. All new gates are independent of G3; framework v1.0.7 remains external frozen. GPU not used/certified.

Run `run_all.cmd HISTORY` for a standalone historical blind PDF/JSON export, or `run_all.cmd ALL` for full validation and official v1.0.7 FREEZE/FULL. `run_all.cmd PARITY` is the inherited C++ kernel parity test.
