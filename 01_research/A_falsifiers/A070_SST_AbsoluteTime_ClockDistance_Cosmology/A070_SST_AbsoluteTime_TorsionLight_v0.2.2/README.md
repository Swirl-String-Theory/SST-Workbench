# A070 (provisional) v0.2.2 - AXIAL TORSION GEOMETRY BLIND CORRECTION

**Status: analytic/synthetic-controls only. NOT native PKLSA; NOT physical photon certification; NOT frozen-framework v1.0.7-certified.**

2026-10-18. Physically selected propagation direction for proposed SST photon torsion pulse: **k parallel straight cylindrical filament axis (theta=0 degrees to axis; theta=90 degrees to the endcap plane).** Distinguish azimuthal twist from axial travel. The earlier v0.2.1 7-angle scan is still valid as a *mathematical inertial-wave control* but is NOT the physically selected torsional-light scan.

## Run

```bat
py -m pip install -r requirements.txt
run_all.cmd SELFTEST
run_all.cmd VERIFY
run_all.cmd AXIAL
run_all.cmd AXIAL_VERIFY
```

The original v0.2.1 synthetic-blind frozen data, contracts and checksums are retained without modification; the new axial mask has its own frozen hash. The REVEAL archive is separate and should only be opened after freezing analysis.

## Key mathematical result

For uniformly rotating incompressible Euler flow, omega_I=+/-2 Omega cos(theta); exact axial k gives **nonzero frequency but ZERO group velocity**. In stationary incompressible Euler fluid, a pure azimuthal perturbation does not propagate by itself; constant U_z advects without intrinsic propagation. These are negative controls, NOT a proof that finite-core PKLSA torsion cannot exist.

Detailed setup `docs/AXIAL_CORRECTION.md`, contract `preregistration/AXIAL_SCIENCE_CONTRACT.json`. The true next step requires independent native 3D finite-core time series and blind phase/energy transport measured along the centerline in comoving coordinates.

## Updated report
`REPORT.pdf` is the v0.2.2 axial audit; the original v0.2.1 report is retained under `docs/REPORT_v021.pdf`.
