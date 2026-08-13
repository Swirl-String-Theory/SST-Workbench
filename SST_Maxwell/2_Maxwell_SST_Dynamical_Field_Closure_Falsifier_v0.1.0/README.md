# Maxwell–SST Dynamical Field Closure Falsifier v0.1.0

Target-blind numerical protocol for three research gates:

1. **DFC-T — transverse-mode theorem:** tests the unreduced dynamics for a massless transverse radiative branch and rejects a finite-frequency longitudinal branch. A transverse projector or gauge-reduced input makes the campaign **INVALID**.
2. **DFC-D — displacement-current micro-closure:** fits the constitutive map from an independently resolved polarization coordinate on 70% of samples and scores the held-out 30%. It independently checks polarization current, bound charge, and continuity.
3. **DFC-G — gravitational interaction-energy deficit:** checks that a single declared Hamiltonian has negative interaction energy for attraction, that `-dU/dd` agrees with an independently reconstructed attractive force, and that absolute energy remains nonnegative within numerical tolerance.

The blind run deliberately does **not** use the measured value of `c`, Newtonian far-field exponents, or an electromagnetic SI target for the fitted polarization coefficient. Those comparisons live in `reveal_targets.py` and are available only after the frozen result hash exists.

## Quick start

```text
python make_synthetic_controls.py
python run_blind.py --campaign examples/positive_control
python reveal_targets.py examples/positive_control/frozen_result.json
```

Expected exit codes: `0=PASS`, `2=FAIL`, `3=INVALID`.

Negative controls:

```text
python run_blind.py --campaign examples/negative_transverse
python run_blind.py --campaign examples/negative_displacement
python run_blind.py --campaign examples/negative_gravity
```

Each should fail the intended gate. The package writes `frozen_result.json` and `frozen_result.json.sha256`; `reveal_targets.py` refuses to operate if the frozen result has been edited.

## Blindness model

This is **procedural target blindness**, not cryptographic secrecy from a person who reads the source code. The intended sequence is:

1. freeze `configs/preregister_v0.1.0.json` and archive its SHA-256;
2. generate solver outputs without feeding target constants/exponents into the solver or model selector;
3. run `run_blind.py` once and archive the frozen result plus hash;
4. only then run `reveal_targets.py` for orthodox comparison.

Changing thresholds, the split seed, channel-independence declarations, or the chosen constitutive model after inspecting results starts a new campaign and must receive a new campaign ID.

## Important physics guards

- `delta p` and `delta rho_E` have the same units but are **not** assumed equal.
- A longitudinal zero-frequency coordinate is not itself a longitudinal radiative wave.
- `J_pol = dP/dt` and `rho_b = -div P` are not falsifiers if they are generated algebraically from the same `P`; independent channels are mandatory.
- DFC-G tests an interaction-energy difference `U_int = H(d)-H(infinity)`. Negative interaction energy is compatible with positive absolute Hamiltonian density.
- Passing these gates validates only the declared closure and source family. It does not derive `e`, `epsilon_0`, `mu_0`, `G`, or the Standard Model.

See `schemas/DATA_CONTRACT.md` for the exact input schema.
