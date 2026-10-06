# A055 Blind Topological Particle Spectrum Falsifier v0.1.1

## Purpose

A055 tests whether low-crossing knot/link geometry produces robust, topology-dependent screening spectra **before** Standard-Model or historical SST/VAM labels are opened.

The blind population is fixed to:

- 35 non-trivial prime knots with crossing number 3–8;
- 47 prime links with crossing number 2–8;
- 82 topologies total.

The corrected historical reveal-only quark hypothesis is

\[
u \leftrightarrow 5_2,\qquad d \leftrightarrow 6_1.
\]

The former `6_2/7_4` note is treated as an erroneous historical note and is not part of the blind model.

## Why v0.1.1 exists

The first A055 run was produced from a source tree still carrying the administrative identifier `A054 v0.1.0`.  Its results exposed three methodological issues that v0.1.1 fixes:

1. `contact_ratio = min_distance / mean_segment` changes explicitly with discretization resolution and therefore cannot be a primary spectral observable;
2. `linking_strength` is undefined for a single-component knot, so replacing its knot value by a small numerical floor creates an artificial mixed knot/link dynamic range;
3. five null targets are far too few to assess a large triplet search.

v0.1.1 therefore adds a resolution ladder, presentation-stability gates, feature-domain masks and 10,000 null trials per valid reveal search.

## Self-contained data

`data/atlas_pd.json` contains all 82 Planar Diagram (PD) presentations.  No KnotPlot, SnapPy, KnotInfo, PKLSA, Google Drive or network access is required at runtime.

The embedded PD data originate from the Knot Atlas `KnotTheory`` database mirror:

- `PD4Knots.m` Git blob `479cede40bab464e22e4516b914a45302f907cce`;
- `PD4Links.m` Git blob `8f54a79591725ddf578877b65021822f48966a02`.

## Blind observables

For each opaque case, deterministic PD-derived 3D presentation embeddings are generated at a resolution ladder

\[
N\in\{40,80,160\}
\]

for the normal `basic` and `full` presets.

The high-resolution aggregate is screened with:

- discrete bending-energy proxy;
- absolute regularized Neumann/Biot–Savart-like line-integral proxy;
- normalized minimum non-local distance;
- absolute component-self-writhe proxy;
- link-only pairwise Gauss-linking-strength proxy.

`contact_ratio` remains in the raw diagnostics but is excluded from pair ranking and SM-ratio searches.

## Feature qualification

For every applicable primary feature \(X\), v0.1.1 requires both a resolution-convergence gate and a presentation-stability gate.

Between the two highest resolutions,

\[
\delta_X
=
\frac{|X_{160}-X_{80}|}
{\max(|X_{160}|,|X_{80}|,10^{-15})}.
\]

The high-resolution embedding ensemble also yields

\[
CV_X=\frac{\sigma_X}{|\bar X|+10^{-15}}.
\]

A feature is qualified only when

\[
\delta_X\le \epsilon_{\rm conv},
\qquad
CV_X\le CV_{\max}.
\]

`basic` uses 8 embeddings/resolution with \(\epsilon_{\rm conv}=0.20\), \(CV_{\max}=0.50\).  `full` uses 16 embeddings/resolution with \(\epsilon_{\rm conv}=0.15\), \(CV_{\max}=0.35\).

## Domain-safe distance spaces

Three independent blind distance spaces are frozen:

| space | population | features |
|---|---|---|
| `common_all` | knots + links | bending, Neumann, minimum distance |
| `knots` | knots only | common features + self-writhe |
| `links` | links only | common features + self-writhe + linking strength |

For pair ranking, each non-negative feature is transformed without an arbitrary epsilon floor via

\[
y=\operatorname{asinh}\!\left(\frac{|X|}{\operatorname{median}(X_{>0})}\right),
\]

then z-standardized within the selected population.

Both raw and fully-qualified pair tables are written.  Historical claims must use the qualified table; a raw rank is diagnostic only.

## Reveal-only mass-pattern search

The reveal layer contains the fixed historical `5_2/6_1` hypothesis and a frozen PDG-2026 mass snapshot.

For a positive qualified scalar feature \(X\), a triplet is allowed one global scale \(s\):

\[
m_i \simeq sX_i,
\qquad
\ln s=\frac{1}{3}\sum_{i=1}^{3}(\ln m_i-\ln X_i).
\]

Its score is

\[
\epsilon_{\log}
=
\sqrt{\frac{1}{3}
\sum_{i=1}^{3}
\left[\ln(sX_i)-\ln m_i\right]^2}.
\]

No post-reveal powers, roots, offsets, \(\pi\)-factors, \(\alpha\)-factors, golden-ratio factors or manually chosen numerical floors are allowed.

### Feature-domain masks

- `bend_energy`, `abs_neumann_energy`, `min_distance`: knot-only, link-only and mixed searches allowed;
- `abs_writhe`: knot-only or link-only; mixed search forbidden;
- `linking_strength`: links only;
- `contact_ratio`: no ratio search.

A zero/non-positive value required by a logarithmic fit is **excluded**, never shifted to `1e-6` or another artificial floor.

## 10,000-trial look-elsewhere null

For each valid feature/pool and target mass triplet, the total log-mass span is fixed while the middle log-position is randomized:

\[
\ln m_1=0,
\qquad
\ln m_2=tS,
\qquad
\ln m_3=S,
\qquad t\sim U(0,1).
\]

The null search uses 10,000 preregistered deterministic pseudo-random \(t\)-values.  v0.1.1 evaluates the exact lower envelope of the candidate error quadratics, so 10,000 trials do not require 10,000 brute-force scans of all triplets.

The full null values are written to `REVEALED/SM_NULL_DISTRIBUTIONS.csv.gz`.

v0.1.1 reports three nested look-elsewhere levels:

1. within one fixed feature/pool (triplet selection corrected);
2. familywise within the common all-atlas features and, separately, across every valid feature/domain search for that SM group;
3. a global null across all preregistered SM triplet groups, valid feature domains and topology triplets.

The global layer is the appropriate diagnostic when highlighting the single most striking match found anywhere in the registered SM search.

## Run

From the falsifier directory on Windows:

```bat
run_all.cmd
```

This runs the `basic` preset.  The stricter production screening is:

```bat
run_all.cmd full
```

To preserve blindness and stop before opening the historical/SM layers:

```bat
run_blind_only.cmd full
```

Then, after independently archiving/reviewing the blind outputs:

```bat
run_40_reveal.cmd full
run_50_package.cmd full
```

A Python-only diagnostic path exists:

```bat
run_python.cmd basic
```

The normal template remains strict C++17 + pybind11 + OpenMP.  `run_all.cmd` fails if the native module cannot build/import or fails Python/C++ numerical parity.

## Output

The run creates:

- `A055_Blind_Topological_Particle_Spectrum_Falsifier_v0.1.1-outputs/`;
- `../A055_Blind_Topological_Particle_Spectrum_Falsifier_v0.1.1-outputs_BLIND.zip`;
- `../A055_Blind_Topological_Particle_Spectrum_Falsifier_v0.1.1-outputs_REVEALED.zip`;
- `../A055_Blind_Topological_Particle_Spectrum_Falsifier_v0.1.1-outputs.zip`;
- SHA-256 sidecars for each archive.

## Interpretation boundary

v0.1.1 is still a **PD-derived screening falsifier**.  It cannot establish a Standard-Model particle assignment.  In particular, it does not yet test Euler equilibrium, finite-core self-confinement, Hessian stability, Kelvin modes, Floquet multipliers, spin, charge, color, weak isospin, couplings, lifetime or scalar Higgs dynamics.

The intended promotion path is A055 v0.2.0:

\[
\text{same blind atlas}
\rightarrow
\text{PKLSA geometry}
\rightarrow
\text{finite-core dynamics}
\rightarrow
\text{Hessian/Kelvin/Floquet}
\rightarrow
\text{same qualified blind/reveal protocol}.
\]
