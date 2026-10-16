PKLSA import is intentionally conservative.

  run_all.cmd PKLSA_IMPORT --pklsa C:\path\to\CANDIDATE_SURFACE.npz

It identifies a closed Nx3 polygon in any NPZ and records a cryptographic file digest,
geometry scale and spacing diagnostics. No qualification of physical 3D dynamics is
implied. The recent Drive PKLSA_SOURCE_NOTES explicitly describes a 300-point KnotPlot
export and regularized Biot-Savart diagnostic (Gamma=1, epsilon=0.12 raw units), not
an Euler trajectory, not a topological stability proof, and not a qualified independent
provider. External geometry file is not bundled so its provenance is never forged.
