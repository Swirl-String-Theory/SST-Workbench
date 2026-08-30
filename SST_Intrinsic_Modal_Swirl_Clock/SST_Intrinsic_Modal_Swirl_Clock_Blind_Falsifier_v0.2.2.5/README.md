# SST Intrinsic Modal Swirl-Clock Blind Falsifier v0.2.2.6

> v0.2.2.6 adds Katlas **link** translation and source-family carrier thresholds. Katlas knots still use explicit braid presentations; Katlas links use the KnotTheory planar-diagram (PD) rotation system to construct a canonical multi-component 3-D embedding. Generated Katlas geometry is always marked translator-derived (`source_coordinates=false`).

## New in v0.2.2.6: links + `--min-carriers`

```bat
run_all.cmd --libraries=Fremlin,Gilbert,Katlas --min-carriers=2
run_all.cmd --libraries=Gilbert,Katlas --min-carriers=2 --kind=links
run_links.cmd
```

`--min-carriers=N` means **N distinct source families for the same topology**. It does not count files. Therefore `3_1`, `3_1p`, and `3_1u` are three Fremlin shape seeds but together only one Fremlin carrier. A link represented by Gilbert and Katlas has two carriers and is eligible for `--min-carriers=2` even though Fremlin has no link source.

Katlas PD translation uses `X[i,j,k,l]` exactly as KnotTheory defines it: labels are cyclic around the crossing starting from incoming lower edge `i`; `(i,k)` is therefore the under strand and `(j,l)` the over strand. The PD rotation system is planarly embedded, the intended crossing gets a local z separation, and each link component is traced independently. The independent Katlas Gauss code must report the same component count or the translated seed is rejected.

Seed-Provenance + Mesh-Certified Modal Clock release.

## Primary question

Stage A asks:

\[
\boxed{\text{Does the same knot/link topology possess a recurrent intrinsic shape mode, and is that result robust to seed provenance?}}
\]

The physical vortex evolution remains regularized finite-core Biot-Savart. Stage B is still candidate-only and asks whether material stretching plus a measured delay provides a core-specific causal mechanism.

## Selectable source libraries

The recommended current campaign is:

```bat
run_all.cmd --libraries=Fremlin,Gilbert,Katlas
```

with roots:

```text
Fremlin   ..\..\Ideal_Fremlin_Fseries\fremlin
Gilbert   ..\..\Ideal_Sources
Katlas    ..\..\Katlas_Sources_v0.2.2_Outputs   (knots + links)
KnotPlot  ..\..\KnotPlot\knots\final   (only when explicitly selected)
```

Accepted selector names are `Fremlin`, `Gilbert`, `Katlas`, and `KnotPlot` (aliases `fseries`, `Ideal`, `KnotAtlas`, `relaxed` are accepted internally). If `--libraries` is omitted the legacy v0.2.2.2 comparison remains available. With an explicit multi-library selection, the physics campaign defaults to the intersection of the selected geometry-capable libraries. Thus `Fremlin,Gilbert,Katlas` does not expand to hundreds of Gilbert/Katlas-only knots.

The user paths

```text
C:\workspace\projects\SST-Workbench\Ideal_Sources\Ideal.txt.gz!\ideal.txt
C:\workspace\projects\SST-Workbench\Ideal_Sources\IdealLinks.txt.gz!\idealLinks.txt
C:\workspace\projects\SST-Workbench\Ideal_Fremlin_Fseries\fremlin\3_1\knot.3_1.fseries
```

are therefore supported without manual extraction. Python reads `.gz` directly.

If `--libraries` is omitted, the legacy relaxed-reference behavior is retained for compatibility. With an explicit selector, unselected libraries are not read. All official Fremlin variants for a matched topology are retained (up to the generous safety cap), while cross-provenance robustness is balanced by source family so multiple Fremlin variants do not receive multiple provenance votes.

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

### Katlas `katlas.json` -> canonical geometry translator

Katlas is information-rich but is not a metric centerline database. v0.2.2.6 therefore separates **source facts** from **generated geometry**. For each supported knot the loader retains its Katlas identity plus compact PD/Gauss/DT/invariant metadata, and reads the explicit presentation

```text
BR(n,{g1,g2,...})
```

when available. The signed Artin braid is embedded as a smooth rectangular braid with crossing height determined by generator sign; its strand permutation is closed outside the braid box with smooth Bezier closure arcs. The resulting seed is tagged

```text
provenance       = katlas
geometry_origin  = generated_from_katlas_braid
source_coordinates = false
translator       = SST-KATLAS-BRAID-1.0
```

so it can never be confused with coordinates supplied by Knot Atlas. In the supplied library this yields 250 unique geometry-capable Rolfsen knots through 10 crossings. 11-crossing PD/Gauss/DT records and 12-crossing DT-only records remain metadata-only in this release; no unreliable DT-to-3D geometry is invented.

Katlas-generated seeds are therefore a **topology-derived canonical-shape provenance**, not an ideal/relaxed metric reference. This is useful for asking whether recurrence depends on Fremlin/Gilbert shape preparation or persists from a neutral topology construction.

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

Thus the scorer can know that several anonymous seeds belong to the same topology without knowing whether it is KnotPlot/Ridgerunner, Fremlin, Gilbert, or Katlas-translated.

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

## v0.2.2.x numerical corrections

### Floating-point mesh-cap tolerance

A controller capped at `1.5` could report `1.5000000000000004` and be rejected by v0.2.1. v0.2.2.2 compares with a declared numerical tolerance (`1e-12` default). This fixes certification bookkeeping only; it does not relax the physical/geometry gate.

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
run_all.cmd --libraries=Fremlin,Gilbert,Katlas
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

Use `run_focus_provenance_3p1.cmd --libraries=Fremlin,Gilbert,Katlas` to compare Fremlin `base/p/u`, Gilbert Ideal, and the Katlas braid-translated trefoil without KnotPlot.

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

## Official source family recognized by v0.2.2.2

When present under `..\..\Ideal_Sources`, the scanner reads the upstream compressed files directly:

- `Ideal.txt.gz` (3--10 crossing knots, `<AB>`),
- `Ideal_11a.txt.gz`, `Ideal_11n.txt.gz` (11 crossing knots, `<HT>`),
- `IdealLinks.txt.gz` (2--9 crossing links, `<TL>`),
- `IdealLinks_10a.txt.gz`, `IdealLinks_10n.txt.gz`,
- `IdealLinks_11a1.txt.gz`, `IdealLinks_11a2.txt.gz`,
- `IdealLinks_11n1.txt.gz`, `IdealLinks_11n2.txt.gz`.

Only topologies present in the relaxed reference catalog enter the default physics campaign; the extra official records remain visible in `SOURCE_SCAN.json` for provenance audit.

Fremlin variants such as `knot.3_1p.fseries` and `knot.6_3z.fseries` are separate shape seeds within the same opaque `fseries` source family.


## Live progress / ETA (v0.2.2.6)
Long campaigns print one START/DONE line per anonymous candidate plus a heartbeat every 15 seconds while a single trajectory is running. The same lines are appended to `outputs/<run>/progress.log`. ETA is intentionally marked with `~`: different geometries can require very different RK4 costs, so it is a forecast rather than a scheduling guarantee. Logging remains blind and therefore never prints the private source library/path/topology before reveal. Change `progress_heartbeat_seconds` in the config if a different heartbeat interval is desired.

### Single-topology focus (v0.2.2.6)
```bat
run_focus_topology.cmd L2a1 --libraries=Gilbert,Katlas --min-carriers=2 --kind=links
```
`--topology` is applied before the carrier-count gate.
