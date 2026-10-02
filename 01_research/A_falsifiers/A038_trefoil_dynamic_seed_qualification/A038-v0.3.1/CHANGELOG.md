# CHANGELOG

## v0.3.1 — Mesh-Gauge Closure Diagnostic (S37B)

Scientific motivation: the v0.3.0 prospective run produced four S35 core-robust seeds but
0/4 S37 mesh-gauge certificates.  Fremlin-like candidates approached mesh-quality failure
at the low feedback rate, while Gilbert-like candidates remained score-stable but showed
materially different final embedded curves across mesh rates.  v0.3.1 diagnoses that
failure without relaxing S37A.

### Added

- **S37B mesh-gauge closure diagnostic** operating on the S35-qualified set even when S37A
  has zero qualifiers.
- Three numerical gauge concepts:
  - `mesh_off`: physical regularized-filament RHS with no mesh velocity;
  - `segment_feedback`: the existing pure-tangential segment-length controller;
  - `target_projection`: an independent pure-tangential controller aimed toward a
    uniform-arclength target.
- Frozen same-RK4-plan comparison across all S37B arms at each resolution.
- Separate diagnostics for:
  - parameterization-invariant embedded-curve distance `D_shape`;
  - raw-label tangential displacement `D_parallel`;
  - raw-label normal displacement `D_perp`;
  - mesh-rate sensitivity and controller sensitivity;
  - empirical error trend `e ~ N^{-p}` across the resolution ladder.
- Default prospective S37B ladder: `N = 64, 96, 128`.
- Production confirmation ladder: `N = 64, 96, 128, 192`.
- `run_37b_mesh_closure.cmd`.
- `run_mesh_closure_from_v030.cmd` for an explicitly **post-hoc, non-certifying** diagnostic
  of an existing v0.3.0 public campaign.
- Explicit canonical-JSON hash-basis metadata on JSON commitments.
- SST falsifier output convention:
  `./SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.1-outputs/`.
- Separate shareable `*_BLIND.zip` and `*_REVEALED.zip`; blind archives exclude sealed
  identities, source audit material and reveal keys.

### Unchanged / fail-closed

- S37A thresholds and qualification logic are unchanged.
- **S37B can never promote a candidate to S40.**
- S40, RPO, Floquet and Phase B still require S37A certification.
- SST Knot Library remains pinned to v0.2.5.
- Physics scope remains the regularized vortex-filament / finite-core surrogate.

## v0.3.0 — pinned KnotRecord integration

- Require exact SST Knot Library v0.2.5 for the designated prospective scientific atlas.
- Freeze Knot Library release/manifest/KAtlas/source-catalog attestations.
- Re-load each generated realization through a portable `KnotRecord`.
- Preserve S37A and downstream fail-closed numerical/physics gates.
