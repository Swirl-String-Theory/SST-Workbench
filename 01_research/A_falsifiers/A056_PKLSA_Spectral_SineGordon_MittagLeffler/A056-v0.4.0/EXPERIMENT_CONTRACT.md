# A056-v0.4.0 dynamic experiment contract

The dynamic-provider schema remains `A056-DYNAMIC-PROVIDER-5`; the scientific change is in A056 G2 scoring, not in the provider file format.

Each paired provider case supplies monotone approximately uniform `t`, `s`, a finite phase field `phi(t,s)`, and a frozen normalized mode envelope `R(t)` or the existing preregistered derived-ringdown fallback. Real-provider metadata includes phase/perturbation/solver/provider identifiers, source/carrier hashes, evidence class, independence unit and provenance family.

Official v0.4.0 E010 campaigns use `paired_kelvin_residual_phase_v1`, `paired_kelvin_mode_envelope_v1`, and `kelvin_m4_eps003_v040_preregistered`. The provider and score JSON files are SHA-256-bound inside `science_contract.json`; editing them after freeze invalidates G0.

The v0.4.0 G2 scoring representation is `circular_fourier_v1`. It changes only spectral admission. The downstream SG/ML fits, holdout fractions, coarsening/certification logic, and ringdown observable remain unchanged.
