# A054 — SST Nucleon Topology Architecture Blind Falsifier v0.1.0

> **Catalog ID note:** `A054` is a candidate allocation based on the 2026-10-06 Drive snapshot: `A053` exists and no named `A054` falsifier family was found. Confirm against the live local registry before merge.

## Research question

Does a collective three-component topology produce target-free dynamical advantages that are absent from matched unlinked controls, and can those advantages be separated from the knot type of the individual components?

This is a **blind tournament**, not a proton/neutron assignment. No mass, charge, Bohr radius, hydrogen binding energy, SST canonical constant, or preferred nucleon identity is available to the blind evaluator.

The reveal-only preregistered hypothesis family is:

| semantic ID | component content | collective architecture | intended comparison role |
|---|---|---|---|
| `C0` | `0_1,0_1,0_1` | unlinked | common null |
| `P_A` | `5_2,5_2,6_1` | unlinked | loose twist-knot architecture |
| `P_B` | `0_1,0_1,0_1` | `T(3,3)` Triple-Gear proxy | pure collective-link test |
| `P_C` | `5_2,5_2,6_1` | decorated `T(3,3)` skeleton | component + collective topology |
| `N_A` | `5_2,6_1,6_1` | unlinked | loose twist-knot architecture |
| `N_B` | `0_1,0_1,0_1` | Borromean closed-braid skeleton | pure irreducible 3-link test |
| `N_C` | `5_2,6_1,6_1` | decorated Borromean skeleton | component + collective topology |

The blind stage never sees those IDs or meanings. It receives shuffled `CAND_<hash>` geometry files only.

## Why this is stricter than a normal topology comparison

The experiment separates two causal axes:

\[
\boxed{\text{component knotting}}\qquad\text{vs.}\qquad
\boxed{\text{collective three-component architecture}}.
\]

Reveal evaluates fixed contrasts rather than selecting the nicest candidate after seeing the results. For example, the collective Triple-Gear contribution at fixed component content is the difference between the decorated and unlinked `5_2,5_2,6_1` cases. The analogous Borromean-skeleton contrast holds `5_2,6_1,6_1` fixed.

No weighted winner score exists in v0.1.0. Every observable remains visible and mandatory hard-gate status is kept separate from exploratory ranking.

## Maximum practical blinding

Preparation is the only stage allowed to know semantic identity. It creates a private mapping and commits its bytes with SHA-256. The public manifest exposes only anonymous geometry IDs, component count, geometry hashes, and opaque circulation-sector labels. Provider identity, topology name, particle interpretation, pairwise linking matrix, and target quantities remain private.

Blind analysis is run without `_private/`. The code computes observables and seals `BLIND_MANIFEST.json`, `BLIND_RESULTS.json`, `ANALYSIS_BLIND.json`, and `REPORT_BLIND.md`. Reveal verifies every hash and the private-map commitment before attaching identity. Reveal never recomputes the physical observables.


### Isolated blind runner

`prepare` also exports `blind_runner/`, an allow-listed evaluator containing only generic geometry loading, finite-core dynamics, numerical analysis and sealing code. It excludes candidate generators, PKLSA semantic selection, the hypothesis table and reveal logic. A semantic-leak scan is hashed into `RUNNER_MANIFEST.json`; the blind stage should be executed from this isolated runner rather than from the full source tree.

A human can of course deliberately reverse-engineer topology from the anonymous coordinates. Therefore v0.1.0 claims **operational/code-level blinding**, not impossible-to-break cryptographic blinding against visual inspection of geometry.

## Upstream PKLSA contract

Runtime authority is the local Workbench:

- E010 PKLSA `v0.3.1`: source/provenance/geometry qualification;
- E011 SKLSA `v0.3.0`: static-ready seed contract and provider anchors.

The current E011 snapshot has materially different evidence states. v0.1.0 runs the **Cartesian provider-anchor envelope** for `5_2` and `6_1`, so every E011 provider anchor participates rather than allowing a convenient representative to determine the answer:

- `5_2`: `STATIC_READY`, `CROSS_PROVIDER_ROBUST`;
- `6_1`: `STATIC_READY`, `CROSS_PROVIDER_SENSITIVE`, with the current provider disagreement reported for \(|Wr|\);
- `L6a4` (Borromean): `STATIC_NOT_READY_E010_EXCLUDED` in this release.

Consequences are fail-closed. Every provider anchor must be retained for `6_1`, and results remain provider-conditional unless they survive the provider envelope. The Borromean hypothesis is therefore **not** presented as an admitted PKLSA `L6a4` source. It is a generated analytic closed-braid skeleton. The Triple-Gear hypothesis likewise uses the existing Workbench `T(3,3)` three-component torus-link proxy rather than claiming tooth/contact mechanics.

`STATIC_READY` is explicitly not `DYNAMICS_READY`.

## Generated topology controls

The Triple-Gear proxy is generated as the standard three-component torus link `T(3,3)`. Each component is an unknot, and the self-test checks that the three pairwise Gauss linking numbers converge to unit magnitude.

The Borromean control is generated as the closure of the standard three-strand braid

\[
(\sigma_1^{-1}\sigma_2)^3.
\]

The self-test checks that its three pairwise linking numbers converge to zero. The three-body topology is intentionally **not** supplied to the blind scorer as a target.

`P_C` and `N_C` are built by a local connected-sum constructor. For each skeleton component it chooses a high-clearance arc, places a cut-open PKLSA knot tangle inside a disjoint insertion ball, reconnects inside that ball, and then verifies that the pairwise Gauss-linking matrix of the three-component skeleton is preserved within the frozen tolerance. Because the skeleton component is an unknot, the connected sum has the source-knot component type, conditional on the sampled clearance certificate.

The constructor is fail-closed: if the insertion ball, bridge clearance, final inter-component clearance, or skeleton-linking preservation test fails, that provider stratum is unavailable and the full tournament cannot become `scientific_ready`. An exact knot-polynomial/isotopy certificate remains a v0.2 certification gate. Missing composite geometry is never replaced by a convenient synthetic curve.

## Common dynamics operator

The starter dynamics is a regularized finite-core Biot--Savart filament operator with no candidate-specific term,

\[
\mathbf u(\mathbf x)
=\frac{1}{4\pi}\sum_j \Gamma_j
\int_{C_j}
\frac{d\boldsymbol\ell'\times(\mathbf x-\mathbf x')}
{\left(|\mathbf x-\mathbf x'|^2+a^2\right)^{3/2}}.
\]

The blind calculation uses normalized geometry and dimensionless circulation. SST SI constants are not available to this stage.

Eight circulation sectors are preregistered under opaque labels `Q0`--`Q7`. They are the Cartesian product of two magnitude normalizations with the four inequivalent three-component sign patterns modulo global sign reversal:

\[
(+++) ,\qquad (-++),\qquad (+-+),\qquad (++-).
\]

The first normalization uses \(|\Gamma_i|=1\) per component; the second uses \(|\Gamma_i|=1/3\), fixing total absolute circulation to unity. Thus CW/CCW assignment is not chosen to favor an architecture, and every candidate is tested under the identical eight-sector ensemble. All sectors remain in the blind ledger; post-hoc selection is forbidden.

The numerical backend is pure NumPy by reference. A C++17/pybind11/OpenMP implementation of the same kernel is supplied; `run_all_extended.cmd` requires the native OpenMP backend. Native/reference agreement is a self-test whenever the extension is built.

## v0.1.0 gates

### G0 — provenance / construction gate

Every source-native component must resolve through the E010/E011 evidence graph with its hashes and provider stratum intact. Generated controls must carry an explicit construction class. Uncertified decorated links are invalid inputs, not physical failures.

### G1 — geometry validity

Closedness, finite coordinates, common arclength resampling, no accidental component intersection and common total-length normalization are prerequisites.

### G2 — relative-equilibrium residual

The induced centerline velocity is fitted to the best rigid-body motion

\[
\mathbf u_i \simeq \mathbf V+\boldsymbol\Omega\times(\mathbf x_i-\mathbf x_c),
\]

and the normalized residual

\[
\epsilon_{\rm RE}
=
\frac{\sqrt{\langle|\mathbf u-\mathbf u_{\rm rigid}|^2\rangle}}
{\sqrt{\langle|\mathbf u|^2\rangle}}
\]

is reported. Lower values indicate a closer relative-equilibrium candidate under this operator; no particle target enters the fit.

### G3 — cross-component causal ablation

The same residual is recomputed with all cross-component Biot--Savart terms removed. Define

\[
\Delta_{\rm cross}
=\epsilon_{\rm RE}^{\rm self-only}-\epsilon_{\rm RE}^{\rm full}.
\]

A positive value means collective interactions improve rigid-motion coherence under the common operator. This is a causal architecture diagnostic, not a nucleon score.

### G4 — short nonlinear retention

The centerlines are evolved with the same RK4 operator. After optimal rigid Kabsch alignment, v0.1.0 records the normalized shape drift. This is only a short-time screen, not the final Kelvin/Floquet certification.

### G5 — topology preservation

Pairwise Gauss-linking matrices are calculated internally at initial/final time. The blind report publishes only the maximum **change**, not the initial topology matrix, reducing semantic leakage.

### G6 — far-field angular anisotropy

On common spherical sampling shells, the diagnostic

\[
\epsilon_{\rm ani}(R)
=
\frac{\operatorname{std}_{\Omega}|\mathbf u(R,\Omega)|^2}
{\langle|\mathbf u(R,\Omega)|^2\rangle_{\Omega}}
\]

is measured. This does not assume that \(|\mathbf u|^2\) is Coulomb or gravity; it is only a target-free measure of how rapidly microscopic anisotropy coarse-grains away.

### G7 — circulation-sector robustness

Both opaque sectors must be evaluated under the same geometry and numerical settings.

### G8 — SO(3) objectivity / source robustness

Rigidly rotated copies must agree numerically. PKLSA provider strata are never pooled across a declared provider-sensitive topology without propagating that sensitivity.

### G9 — convergence

Resolution/core-radius ladders are compared. Numerical non-convergence produces

`INCONCLUSIVE_NUMERICAL`,

not a physics `FAIL`.

## Explicitly deferred from v0.1.0

Full Kelvin/Floquet certification is deferred until a link-capable independent modal producer exists. The recent electron tournament already identified that current dynamic-eigenmode handoff is trefoil-first rather than symmetric across arbitrary links. Likewise, mass, charge, Coulomb/torsion closure, atomic binding and gravity are not used here. Those become downstream falsifiers only after a nucleon geometry survives this architecture screen.

## Status semantics

`SURVIVES_BLIND_SCREEN` means only that the candidate survived the preregistered v0.1 numerical/dynamical gates. `FAIL_DYNAMICAL_CONFINEMENT` and `FAIL_TOPOLOGY_PRESERVATION` are physical failures only after numerical qualification. `INCONCLUSIVE_NUMERICAL` remains logically distinct from both. `PREPARED_PARTIAL_FAIL_CLOSED` means the campaign is useful for controls/planning but is not a complete nucleon tournament.

## Workbench placement

```text
01_research/A_falsifiers/
  A054_nucleon_topology_architecture_blind_falsifier/
    FAMILY.yaml
    A054-v0.1.0/
```

The repository candidate should be merged only after the local registry confirms that `A054` is still the next free A-family identifier.

## Running

From `A054-v0.1.0`:

```cmd
run_all.cmd C:\workspace\projects\SST-Workbench
```

This installs, self-tests, prepares and runs the basic blind stage, then **stops before reveal**.

Extended native run:

```cmd
run_all_extended.cmd C:\workspace\projects\SST-Workbench
```

Reveal is deliberately separate:

```cmd
run_99_reveal.cmd path\to\campaign
```

Blind packaging:

```cmd
run_90_pack_blind.cmd path\to\campaign
```

## Output convention

```text
A054_Nucleon_Topology_Architecture_Blind_Falsifier_v0.1.0-outputs/
  basic_YYYYMMDD_HHMMSS/
  extended_YYYYMMDD_HHMMSS/
```

Each campaign contains a private commitment, anonymous inputs, blind results, blind analysis/report, and a cryptographic seal. Reveal adds identity and preregistered contrasts only after seal verification.

## Current v0.1.0 implementation boundary

The included analytic controls are runnable now. Source-native loose and decorated twist-knot cases are prepared only through the exact local E010-v0.3.1 loaders, with both raw-source and `PKLSA-GEOMETRY-SHA256-v1` checks before A054 resampling. Every `5_2` × `6_1` provider-anchor combination becomes its own private stratum. A local run may still legitimately stop as `PREPARED_PARTIAL_FAIL_CLOSED` if any upstream anchor cannot be resolved or any connected-sum certificate fails; that is scientifically preferable to silently fabricating geometry.
