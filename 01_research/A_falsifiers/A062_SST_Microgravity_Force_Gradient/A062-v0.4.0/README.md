# A062-v0.4.0: Resolved Vortex-Tube Energy / Transport / Gravity Source Closure

**Release scope:** new falsifier, not a modification of v0.1.0-v0.3.0. Bundle includes genuine unmodified SST Framework v1.0.8 LOCAL_VALIDATED_CANDIDATE.

## Hypotheses
H0: Two raw E011 STATIC_READY trefoil geometries can each be converted into a smooth, closed, Gaussian-vorticity tube with finite nonzero kinetic energy.
H1: The earlier SST-73 localized tensor double-divergence candidate has no monopole in boundary-free smooth free space.
H2: The positive kinetic-energy density furnishes an optional, nonzero E/c² *candidate* gravitational source (but no independently derived scalar dynamics, K or equivalent test-body response).
H3: Helicity/conserved topology and instantaneous finite-core Gaussian kernels do not by themselves qualify a stationary/long-lived dynamic knot; viscosities/forcing and full Euler/NS time evolution are deferred.

## Windows from Workbench root
Copy the contents of `SST-Workbench_DISTRIBUTION` into your existing Workbench root, retaining the original v1.0.8 framework in its canonical template folder.
Then use:

    cd 01_research\A_falsifiers\A062_SST_Microgravity_Force_Gradient\A062-v0.4.0
    python -m pip install -r requirements.txt
    python -m pytest -q tests
    run_all.cmd FREEZE
    run_all.cmd CERTIFY

`run_all.cmd FREEZE` runs `init_private.py` **before** freezing; nonce/key are only made when absent and no existing commitment has been recorded. Never rekey an already frozen instance.

Framework v1.0.8 gives each new FULL/CERTIFY run a unique run-ID. Source package includes neither nonce nor generated commitments. `G4 FAIL` (localized SST-73 transport monopole) does NOT skip G5-G8.

## Linux
    python -m pip install -r requirements.txt
    PYTHONPATH=. python -m pytest -q tests
    python init_private.py
    python run_instance.py FREEZE
    python run_instance.py CERTIFY

If shared framework is unavailable or mismatched, bootstrap fails closed.

## Scientific caution
- Gaussian cloud is a *spatially resolved smooth vorticity field* defined as a line convolution with finite width; kinetic energy is computed from the exact Gaussian-smoothed Green's function. This is not a resolved time-dependent Euler/Navier-Stokes simulation or dynamically proven stationary knot.
- `a_core/reach` and `L_phys = r_c/reach` are diagnostic scale assumptions. Later Canon clearly distinguishes `a_core` and `r_c`.
- E/c² is energy-equivalent mass, not automatically passive or active gravitational mass. Using ρ_core as ambient fluid density is physically invalid unless separately derived.
- Prior SST-47/49 scalar Poisson law returns R^-2 *conditionally*. New version tests energy-source existence and alternative SST-73 transport, not universal gravity proof.
- Google Drive SST paper inventory has 144 items and a 91-slot SST-00...90 index. Indexed documents are not claimed to be read or tested; see `KNOWLEDGE_MAP.md`.
- Old SST-28 is excluded.
- External Navier-Stokes singularity constructions are not implemented or assumed as proofs.

## Results
Framework outputs named `sst_microgravity_force_gradient_v0.4.0-outputs`. Files contain `V040_SCIENCE_RESULTS.json`, `V040_SCIENCE_GATES.json`, `V040_ENERGY_REFINEMENT.png`, and actual independent C++ parity logs. Framework also produces gate ledger and unique BLIND ZIP and PDF exports. No experimental discovery is withheld.
