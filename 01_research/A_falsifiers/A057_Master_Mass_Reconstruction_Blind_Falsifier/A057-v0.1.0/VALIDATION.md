# A057 v0.1.0 validation status

**Build status:** assembled and locally source-validated.  
**Framework target:** SST Falsifier Framework v1.0.6 `CANONICAL_FROZEN`.  
**Production physics status:** not run in this build container because the live Windows SST-Workbench/E010 source tree is not mounted here.

Local validation performed before packaging:

1. Python syntax compilation for all A057 modules.
2. Unit tests for closed-curve resampling, doubly-critical reach normalization, energy-matrix symmetry, core-tube quadrature, Hessian/Jacobian construction, and diagnostic-continuation semantics.
3. JSON schema/required-field checks matching the v1.0.6 science/source/gate contracts.
4. Public-tree scan against the committed protected numeric tokens.
5. Pure C++17/OpenMP core-kernel selftest compilation on the build host, plus precomputed nonced BLIND/REVEAL commitments and immutable `FROZEN_PROTOCOL.json`.

Target-machine acceptance still requires `run_00_install.cmd` followed by at least `run_all.cmd FULL`; `CERTIFY` is the publication-grade campaign.

6. Synthetic end-to-end diagnostic-continuation smoke with a minimal fake PKLSA tree: `G16=FAIL` and `G18=FAIL` were followed by executed `G17`, `G19`, `G20`, `G21`, and `G22`; unavailable native/GPU lanes were `UNRESOLVED` without stopping later gates. This is implementation evidence only.
