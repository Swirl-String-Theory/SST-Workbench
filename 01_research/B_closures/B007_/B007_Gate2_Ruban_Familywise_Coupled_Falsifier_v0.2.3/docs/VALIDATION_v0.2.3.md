# Validation v0.2.3

Package tests: 57/57 passing with real dataset paths enabled. Includes v0.2.2 legacy regression tests, rigid transform invariance, nonrigid deformation detection, exact nested analytic source consistency, source SHA-256 validation and short paired-integrator regression.

Two end-to-end executions on source-verified datasets:
- `B007_V023_SMOKE_B020_128_256`: real source N2048/4096; dynamics N128/256; explicitly reduced-resolution-only.
- `B007_V023_NATIVE_FINAL_VALIDATION`: real source and dynamics N2048/4096; nsteps 1/2 to verify native pair integration and two-level gate plumbing; T*=0.0001. Technical smoke, not dynamics qualification.

The scientific question of robust finite-time growth remains unresolved; no 121x2 native production campaign is claimed. Long-time tests, additional spatial/time refinements, full Euler and topology-preserving dynamics are not performed.
