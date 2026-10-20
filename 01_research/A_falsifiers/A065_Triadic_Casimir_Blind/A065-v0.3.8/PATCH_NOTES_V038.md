# v0.3.8
- Added geometry-derived Gaussian 3D vortex-tube surrogate, three-component omega volume NPZ, spectral solenoidal velocity, periodic pressure Poisson diagnostic.
- Local Frenet-free tangent/normal sections with circulation/enstrophy and strict strand contamination gates; Gaussian-conditional a inversion and optional Rosenhead equivalence labels.
- Dependent synthetic withheld velocity/pressure predictions. Negative results G29/G31 are retained. Physical G32 remains UNRESOLVED.
- Added `CORE3D` standalone runner and import-audit interface; extended official v1.0.7 instance with G28..G32 without changing the frozen runtime, protected hashes, historical G2/G11/G13/G24.
- No independent source-native Euler/PKLSA snapshot, no modeled time evolution, no physical constants; requires external solver and separate heldout provider.
