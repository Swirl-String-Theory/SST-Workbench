# SST Intrinsic Modal Swirl-Clock Blind Falsifier v0.2.2

Seed-Provenance + Mesh-Certified Modal Clock release.

## Primary question

Stage A asks:

\[
\boxed{\text{Does the same knot/link topology possess a recurrent intrinsic shape mode, and is that result robust to seed provenance?}}
\]

The physical vortex evolution remains regularized finite-core Biot-Savart. Stage B is still candidate-only and asks whether material stretching plus a measured delay provides a core-specific causal mechanism.

## Default source families

`run_all.cmd` now compares matched topologies from:

```text
relaxed   ..\..\KnotPlot\knots\final
fseries   ..\..\KnotPlot\Knots_FourierSeries
ideal     ..\..\Ideal_Sources\Ideal.txt or Ideal.txt.gz
links     ..\..\Ideal_Sources\IdealLinks.txt or IdealLinks.txt.gz
```

The user paths

```text
C:\workspace\projects\SST-Workbench\Ideal_Sources\Ideal.txt.gz!\ideal.txt
C:\workspace\projects\SST-Workbench\Ideal_Sources\IdealLinks.txt.gz!\idealLinks.txt
C:\workspace\projects\SST-Workbench\KnotPlot\Knots_FourierSeries\3_1\knot.3_1.fseries
```

are therefore supported without manual extraction. Python reads `.gz` directly.

By default v0.2.2 uses the relaxed catalog as the reference topology set. It does **not** add unrelated Ideal/Fourier knots merely because they exist in the source archives. At most one seed per `(topology, provenance)` is retained in BASIC unless the config is changed.

## Source reconstruction

### Fremlin `.fseries`

The compact six-column convention is read as

```text
ax bx ay by az bz
```

per harmonic `n=1,2,...`, corresponding to

\[
\mathbf X(t)=\sum_{n\ge1}\left[\mathbf A_n\cos(nt)+\mathbf B_n\sin(nt)\right].
\]

An optional leading 3-column constant vector is accepted as `A0`.

Example topology naming supported includes:

```text
3_1\knot.3_1.fseries  -> K3.1
knot_T2.3.fseries     -> T2.3
```

### Gilbert `Ideal.txt` / `IdealLinks.txt`

The Gilbert representation is reconstructed directly:

\[
\mathbf X(t)=\frac{\mathbf A_0}{2}+\sum_{n\ge1}\left[\mathbf A_n\cos(nt)+\mathbf B_n\sin(nt)\right].
\]

Omitted coefficients remain zero.

Gilbert IDs are mapped exactly, e.g.

```text
3:1:1 -> K3.1
5:1:2 -> K5.2
2:2:1 -> L2.2.1
9:2:20 -> L9.2.20
```

`IdealLinks.txt` `<STRING>` blocks are **not concatenated**. Every string is kept as an independent closed filament component. The indexed C++/pybind11 kernel evaluates self- and mutual-component Biot-Savart interactions and closes each component separately, so there is no fictitious bridge segment between link strings.

## Blinding

Primary scoring sees opaque identifiers only:

```text
carrier_id
topology_group_id
pair_id
probe_arm
n_components
certification_priority
```

The following remain private until reveal:

```text
topology_id
provenance
source_path
source_name
source_record_id
source_scale
physical_probe_sign
```

Thus the scorer can know that several anonymous seeds belong to the same topology without knowing which is Ridgerunner, Fremlin or Gilbert.

## v0.2.1 numerical fixes retained

- `T_A=24` BASIC and fixed absolute discovery interval `0 <= t <= 1.2`.
- natural and odd-response modal channels.
- per-snapshot arclength canonicalization before POD.
- tangential segment-feedback mesh redistribution.
- strict certification gate `ds_cv <= 0.20`.
- coverage-aware global negative verdict.
- candidate-only mesh-gauge replay.
- Stage B has no remeshing and restores material segment meaning.
- hard `dt ~ ds^2` policy; step caps never silently enlarge `dt`.
- MSVC-safe `py::ssize_t`.

## v0.2.2 numerical corrections

### Floating-point mesh-cap tolerance

A controller capped at `1.5` could report `1.5000000000000004` and be rejected by v0.2.1. v0.2.2 compares with a declared numerical tolerance (`1e-12` default). This fixes certification bookkeeping only; it does not relax the physical/geometry gate.

### Stronger but audited mesh controller

Complex relaxed knots repeatedly saturated the old 1.5× mesh/physical RMS cap. BASIC now uses nominal:

```text
mesh_redistribution_rate = 4.0
mesh_max_relative_rms    = 2.0
```

A provisional clock is replayed at low/high mesh gauges. Both controller gain and cap are varied:

\[
(\kappa,c)_{\rm low}=0.7(\kappa,c)_0,
\qquad
(\kappa,c)_{\rm high}=1.3(\kappa,c)_0.
\]

The frozen mode must remain recurrent and period/closure/amplitude must remain within the predeclared spread gates.

### Multi-component mesh quality

For links, `ds_cv` is calculated per component and the **maximum component CV** is used. Different link components are not penalized merely because their physical lengths differ.

## Seed-provenance robustness gate

After mesh-gauge certification, anonymous variants of one topology are compared.

A provenance-robust clock requires by default:

- at least 2 seed variants for the topology;
- at least two thirds of available seed variants to contain a certified recurrent clock;
- all compared variants geometry-valid;
- matching natural/odd channel;
- relative candidate-period spread <= 30%.

Possible provenance outcomes include:

```text
PASS_SEED_PROVENANCE_ROBUST_RECURRENT_SHAPE_CLOCK
PASS_SINGLE_SEED_SHAPE_CLOCK__FAIL_OR_INDETERMINATE_PROVENANCE_ROBUSTNESS
INDETERMINATE_STAGE_A_INSUFFICIENT_VALID_COVERAGE
FAIL_STAGE_A_NO_RECURRENT_SHAPE_CLOCK
```

A PASS confined to only one representation is therefore explicitly classified as seed-shape-specific rather than immediately promoted to a topology-level clock.

## BASIC chain

```bat
run_all.cmd
```

runs:

```text
setup
native MSVC/OpenMP build
selftest
source/provenance scan
1  prepare matched relaxed/fseries/Ideal/IdealLinks -/0/+ arms
2  nominal Stage A, T=24
3  frozen early-POD recurrence analysis
4  low mesh-gauge replay on provisional candidates
5  high mesh-gauge replay on provisional candidates
6  mesh-gauge certification
7  blind seed-provenance robustness
8  material-core Stage B on certified candidates
9  fixed-core Stage B null
10 causal/core-specificity analysis
```

Before the long run you can inspect source discovery only:

```bat
run_setup.cmd
run_provenance_scan.cmd
```

which writes:

```text
outputs\SOURCE_SCAN.json
```

## Fast trefoil provenance test

To test exactly the topology for which the supplied Fremlin path is known:

```bat
run_setup.cmd
run_build_native.cmd
run_focus_provenance_3p1.cmd
```

This compares matched `K3.1` relaxed/Fremlin/Ideal representations using the same `T=24` recurrence and mesh-gauge gates.

## Relaxed-only compatibility

The earlier single-source path remains available:

```bat
run_all_relaxed_only.cmd
```

This exists for A/B comparison with v0.2.1; `run_all.cmd` itself now means the provenance campaign.

## Key outputs

```text
outputs\SOURCE_SCAN.json
outputs\basic\analysis\blind_stage_a_summary.json
outputs\basic\analysis\blind_stage_a_carrier_summary.csv
outputs\basic\analysis\blind_stage_a_modal_results.csv
outputs\basic\analysis\blind_stage_a_gauge_summary.json
outputs\basic\analysis\blind_provenance_results.csv
outputs\basic\analysis\blind_provenance_summary.json
outputs\basic\analysis\blind_stage_b_results.csv
outputs\basic\analysis\blind_summary.json
```

Review these blind first. Then:

```bat
run_reveal.cmd outputs\basic
```

also writes:

```text
outputs\basic\analysis\revealed_provenance_results.json
```

with the actual relaxed/fseries/ideal labels joined back in.

## Interpretation

A representation-specific PASS means a dynamically favorable **shape** was found, not yet a topology-invariant swirl clock. A cross-provenance PASS is stronger because the same topology supports compatible recurrence from independently prepared centerlines. Stage B is stronger again and is required before claiming evidence for the proposed stretching/return-phase/core-feedback mechanism.
