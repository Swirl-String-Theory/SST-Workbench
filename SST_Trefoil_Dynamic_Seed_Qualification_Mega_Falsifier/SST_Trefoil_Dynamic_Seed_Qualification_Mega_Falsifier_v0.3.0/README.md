# SST Trefoil Dynamic Seed Qualification Mega Falsifier v0.3.0

## Purpose

v0.3.0 preserves the v0.2.2 numerical/physics gates and adds a strict input/provenance
boundary through **SST Knot Library v0.2.5**. Scientific runs no longer trust a source
filename, ad-hoc XYZ parser, or manually declared family as sufficient input evidence.
Every generated atlas realization is bound to a recomputable `KnotRecord` before scoring.

The model scope remains the regularized vortex-filament / finite-core surrogate. This
release does **not** establish physical SST, a stable trefoil RPO, a publication-ready
Floquet certificate, or a causal mechanism.

## Historical v0.2.2 result retained

The supplied Codex v0.2.2 campaign remains `INDETERMINATE`: four candidates passed
resolution/temporal/core checks, **0/4 passed S37 mesh-gauge**, and consequently no
eligible S40-S60/Phase-B trefoil trajectory existed. v0.3.0 does not relax S37 or rescore
that campaign.

## Pinned knot-library dependency

Scientific atlas config requires:

```text
sst-knot-library/0.2.5
```

Default repository-relative location:

```text
Knot_Library\SST_Knot_Library\SST_Knot_Library_v0.2.5
```

or set:

```powershell
$env:SST_KNOT_LIBRARY_HOME = 'C:\...\SST_Knot_Library_v0.2.5'
```

Before any atlas seed is generated, the falsifier verifies the library release identity,
full manifest, KAtlas snapshot and source-catalog hashes. These hashes are frozen into the
preregistration and run evidence.

## Topology status

The atlas requires both:

1. pinned KAtlas reference topology `3_1` through SST Knot Library; and
2. the independent float64 three-crossing trefoil witness at N=64,96,128.

That status is intentionally named:

```text
SUPPORTED_NUMERICAL_DIAGRAM_NOT_EXTERNAL_PROVIDER_CERTIFIED
```

A KAtlas label/reference is not external certification of a supplied space curve.
Publication-oriented topology certification therefore remains a separate gate.

## One-click prospective campaign

From this package directory:

```bat
run_all_atlas.cmd C:\workspace\projects\SST-Workbench
```

Optional explicit outputs:

```bat
run_all_atlas.cmd <repo-root> <atlas-output> <campaign-output>
```

The script performs:

```text
setup -> native C++/pybind build -> selftests
      -> pinned Knot Library verification
      -> atlas freeze
      -> test-realization generation + KnotRecord binding
      -> blind S20/S30/S32/S35/S37/S40/S50/S60 screen
      -> gated Phase B
      -> reveal verification
```

Outputs are fail-closed and never overwritten.

## Source lineages in the designated atlas

- Fremlin local `.short` coordinate source;
- Brian Gilbert / SONO Fourier source;
- SST Knot Library constructive KAtlas-braid trefoil.

These are three **construction lineages**, not three statistically independent physical
observations. Parent-level held-out status remains false.

## Key files

- `config/prospective_atlas.json` — frozen scientific screen config;
- `config/phase_b.json` — Phase-B shooting/monodromy/intervention protocol;
- `src/sst_seed_falsifier/knot_library.py` — pinned dependency + portable KnotRecord bridge;
- `docs/KNOT_LIBRARY_INTEGRATION_v0.3.0.md` — trust boundary;
- `docs/CODEX_V0.2.2_EVIDENCE_AUDIT.md` — historical evidence interpretation;
- `docs/PHASE_B_LIMITS.md` — remaining Phase-B limits.

## Safety / interpretation

Do not call a KAtlas braid seed `ideal`. Do not treat `UNVERIFIED` library topology as
`CERTIFIED`. Do not relax S37 after seeing a failed campaign. Do not infer full 3D Euler
stability from this filament surrogate. Do not reuse a scored test shard as new holdout
evidence.
