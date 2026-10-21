# CHANGELOG

## v0.3.0 DEVELOPMENT — 2026-10-20

### Source analysis added
- SST-33 `Coherence-Enhanced Heat Transport...`: checked Lorentzian kernel, damping/units, and conditional thermal-bar signal.
- SST-33 `Comparative Thermodynamics...`: retained harmonic strain as mechanical coordinate; separated from equilibrium temperature and heat capacity.
- SST-35 `Resonance-Matched Excitation`: repaired explicit peak-amplitude Gaussian/Lorentzian normalization; added numerical quadrature and Fisher diagnostics.

### Computational additions
- Introduced isolated clearly marked finite-core filament **surrogate**, explicit 0_1 ring and 3_1 trefoil geometry, RK4 short evolution, energy proxy, impulse, ring refinement.
- Added 55 new local tests. Preserved and executed 47/47 original v0.2.0 tests.
- Added figures, CSV and JSON diagnostic outputs, scriptable native-manifest provenance precheck, and explicit blocked status for source-native PKLSA.

### No claims upgraded
- Full 3D Euler--director PDE, PKLSA engine native dynamics, quantum clock, photon speed, heat flux microphysics, gravity and charge remain NOT RUN/UNRESOLVED.
