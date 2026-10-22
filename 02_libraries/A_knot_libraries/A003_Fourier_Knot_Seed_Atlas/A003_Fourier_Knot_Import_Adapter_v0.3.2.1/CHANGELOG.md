# v0.3.2.1 — G5 receipt transfer repair (2026-10-21)

- Repaired **only** the G6/G5 receipt adapter-version compatibility bug. Live v0.3.2 G5 runs had 32 measured pyknotid observations, ten PASS gates and valid ledger hashes, but were incorrectly rejected by a version whitelist ending at 0.3.1.
- Allowlist is now exact for 0.2.8.1, 0.2.9, 0.3.0, 0.3.1, 0.3.2, and 0.3.2.1. Unknown future versions still FAIL CLOSED.
- G5 receipt discovery handles v0.3.2.1-outputs / v0.3.2-outputs and historical directories; new outputs use a create-only v0.3.2.1-outputs folder.
- Regression tests check real v0.3.2 receipt source bytes separately from synthetic negative controls. No historical output, Framework, E010, C005, knot atlas, prior gate acceptance threshold, or numerical solver is changed.
- G6P8 and G6P9 remain UNRESOLVED; G6 is not promoted.

---

# A003 Fourier Knot Import Adapter — v0.3.2

**Parent:** v0.3.1. Historical releases, immutable atlas and v1.0.10 Framework untouched.

## Added

- `G6P14` — segment/segment clearance at every one of the 17 actual RK4 step endpoints per seed and mesh, plus a *rigorously sufficient* no-contact lower bound for the **piecewise-linear polygonal interpolation** between successive computed states. A positive result does **not** enclose the exact ODE path and is not continuous Euler topological certification.
- `G6P15` — genuinely independent SciPy DOP853 trajectory integration vs v0.3.1 classical RK4 using the *same authentic C005 v0.6.1 operator*. Solver-independence, not model/data independence.
- `G6P16` — opt-in explicitly SHA-256-pinned, provenance-separated external KnotPlot/Gilbert-style XYZ carrier manifests. No automatically fabricated or inferred independent families. Geometric resampling and topological checks recorded. Absent provider families: `UNRESOLVED`.
- `G6P8` — create-only persistent E010 source-contract/index proposals, readback check, and refusal to modify E010 v0.3.1 canonical package. Proper closure requires separately versioned E010 release with registered carrier API and provenance/freeze attestation.
- `G6P9` — explicit physical continuum Euler/pressure-Poisson gap ledger, never a surrogate PASS.
- New scripts, 13 specialized tests, development diagnostic, and a historical v0.3.1 trajectory replay.

## Gates

Numerical `G6P14` may PASS with the qualification `INTERPOLANT_ONLY` **without** `G6` passing. `G6P15` may PASS as `NUMERICAL_SOLVER_ONLY`; `G6P16` requires external provenance; `G6P8/G6P9` remain UNRESOLVED without new independent scientific/registry authority. G6 physical result remains UNRESOLVED.

## Preregistration / limits

Freeze C005 epsilon 0.05 atlas units, T=2, N=[150,300,600,1200], RK4 16 steps at all meshes, five quarter-time topology snapshots, and corrected pyknotid==0.5.3. DOP853 rtol=1e-9, atol=1e-11. G6P14 uses all 16 intervals; geometric distance lower bound = min segment clearance at start - 2*max vertex displacement; only provably valid for **linear-in-time interpolation**. No temporal adaptive escalation or interval arithmetic true-ODE proof in v0.3.2.
