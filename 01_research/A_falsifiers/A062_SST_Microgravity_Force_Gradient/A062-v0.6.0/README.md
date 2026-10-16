# A062-v0.6.0 — Constitutive Gravity Source, Green Response & Equivalence Gates

**Purpose:** Go beyond A062-v0.5.0 short-time Euler/NS dynamics and test the *source-to-field* part of a gravitational closure without importing physical Newton G or assuming source equals passive mass.

## Exact split in the protocol

1. Reproduce the static source-pinned E011 finite Gaussian tube and v0.5.0 periodic Euler/NS calculation unchanged.
2. Regenerate dimensionless **u(x,t)** for both upstream providers at t=0 and final t, each with nu=0 and nu=0.005; check the energy against the user's Windows-v0.5.0 results copied as read-only provenance.
3. Compute positive conditional active `q(x)=0.5|u(x)|^2` and `Q=int q dV`. This is **hydrodynamic kinetic energy**, not experimentally established gravitational source mass.
4. Introduce an explicitly **postulated** isolated scalar Poisson equation with dimensionless `K=1`: `laplacian Phi=4*pi*K*q`, `Phi=-K*int q(x)/|R-x| dx` and `g=-grad Phi`. Report `1/R^2` but **never call the slope a hydrodynamic derivation**: it follows from the assumed Green kernel.
5. Free-space Green kernel is verified against an analytic finite 3D Gaussian source and an independently compiled C++17 potential/gradient worker.
6. Local algebraic clock `S=sqrt(1-u^2/c_ref^2)` is separately tested: absent an independent nonlocal mediator it cannot propagate a long-range gravitational monopole. **G14 FAIL only for this restrictive local mapping.**
7. Preserve the existing **G4 FAIL** for isolated SST-73 stress-double-divergence and distinguish the zero-mean periodic Poisson problem from the isolated-cell free-space *assumption*.
8. Leave **G8, G11, G15, G16, G18 UNRESOLVED** until a real clock-field action, test-body response, independently derived SI `G`, isolated dynamical knot and withheld experiment exist.

## Blindness, reproducibility

Same unchanged framework `v1.0.8 LOCAL_VALIDATED_CANDIDATE`, no private nonce or HMAC keys in distribution. Nonce/opaque key are generated only for a genuinely unfrozen instance by `run_all.cmd FREEZE`. Unique run IDs prevent overwrites. `G6` is reserved for SYCL and remains `NOT_APPLICABLE`. The known v1.0.8 manifest-hash report-ordering issue is not repaired by changing the frozen framework.

### Windows

```bat
python -m pip install -r requirements.txt
python -m pytest -q tests
run_all.cmd FREEZE
run_all.cmd CERTIFY
```

### Linux

```bash
python -m pip install -r requirements.txt
python -m pytest -q tests
bash run_all.sh FREEZE
bash run_all.sh CERTIFY
```

Outputs include `V060_GRAVITY_RESULTS.json`, `V060_GRAVITY_GATES.json`, `V060_CONDITIONAL_FARFIELD.png`, `V050_DYNAMIC_RESULTS.json`, `V050_SCIENCE_RESULTS.json`, native C++ reference and framework gate ledger / PDF.

**Scientific warning:** The free-space lift of a periodically evolved source uses an isolated-cell interpretation not justified by a free-space Euler/NS solution. `K=1` is unit normalization, **not measured G**. Failure to derive universal gravitational coupling is a genuine open physics gate, not a reason to alter preregistered thresholds.
