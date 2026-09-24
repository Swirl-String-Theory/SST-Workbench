# SST Euler Regularity / BKM Singularity Gate v0.2.0 (A043)

**PKLSA population integration release.** This version replaces the single synthetic T(2,3) seed path as the primary campaign input with the complete 48-member PKLSA `knot_3.1` / PTSA v1.0.0 trefoil population.

## New in v0.2.0

- provenance-aware PKLSA v0.1.1 adapter;
- signed bundle SHA-256 verification for `families/14_knot_3p1.npz`;
- generic C++17/pybind11 centerline-to-vorticity-tube kernel;
- common closed-arclength/centroid/uniform-scale canonicalization;
- fresh salted blind geometry/case IDs;
- dependency-aware accounting: 48 shape cases != 48 independent sources;
- convergence is now assessed only across replays of the **same geometry**;
- full 48-case BASIC screen plus a 3-geometry smoke config and a 3-resolution certification template.

## PDE

The dimensionless solver remains the 3-D incompressible unforced Euler system on a periodic cube,

\[
\partial_t\mathbf u=\mathbb P(\mathbf u\times\boldsymbol\omega),\qquad
\boldsymbol\omega=\nabla\times\mathbf u,\qquad \nabla\cdot\mathbf u=0,
\]

with RK4 and 2/3 de-aliasing.

## PKLSA input contract

Pass the root folder of `SST_Parametric_Knot_Link_Seed_Atlas_v0.1.1`. It must contain at least:

```text
manifests/CANDIDATES_FULL.jsonl   (or .csv)
families/14_knot_3p1.npz
```

The scientific configs verify the known signed bundle hash. See `docs/PKLSA_INTEGRATION.md`.

## Run

```cmd
run_all.cmd "C:\path\to\SST_Parametric_Knot_Link_Seed_Atlas_v0.1.1"
```

or set `SST_PKLSA_ROOT` and run `run_all.cmd`.

Configs:

- `config/pklsa_basic.json`: all 48 shapes, single-resolution population screen;
- `config/pklsa_smoke.json`: variants 0/23/47, software smoke only;
- `config/pklsa_certification_template.json`: all 48 shapes at N=32/48/64; expensive certification template.

## Interpretation guard

`NO_CONVERGED_BKM_CANDIDATE_IN_WINDOW` means only that no tested geometry passed the preregistered finite-window numerical escalation gate. It does not establish global Euler regularity.

The 48 PKLSA trefoils form one dependent PTSA/PKLSA shape population. Population coverage can test robustness across shape space, but does not multiply provenance strength by 48.

## Blind/reveal

BLIND excludes candidate IDs, variant indices, PTSA IDs, parameter triples and SST constants. SST constants enter only in the post-hoc REVEALED scale mapping.
