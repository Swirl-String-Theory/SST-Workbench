# Blinding protocol

The blind campaign is target-free rather than merely hiding a printed label.

Before any gate runs, the program:

1. parses the selected JSON config;
2. rejects forbidden benchmark keys (`h`, `hbar`, Planck-related target keys, `c_m_s`, `alpha`, fine-structure target keys);
3. hashes the frozen config;
4. hashes all Python/C++ evaluator sources;
5. hashes every loaded external curve array;
6. writes `blind_manifest.json` and `frozen_config.json`;
7. only then executes E3 → E4 → E5 → E2 → E1.

The blind evaluator is allowed to use SST canonical quantities that define the simulated substrate scale, including `r_c`, `rho_f`, and `v_swirl`. It is not allowed to compare derived observables with external target constants.

Specifically:

- E4 outputs `J_blind = DeltaE/nu` in J s but does not know a target action.
- E5 outputs `C_blind = sqrt(DeltaE/DeltaM)` in m/s but does not know a target speed.
- E1 fits its own event spacing `q` from training data and tests it on held-out data plus continuous surrogates; it has no photon-energy target.

Any later unblinding must occur in a separate analysis after the result directory, manifest and protocol hash have been archived.
