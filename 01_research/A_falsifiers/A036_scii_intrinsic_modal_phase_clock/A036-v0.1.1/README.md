# SST SC-II Intrinsic Modal Phase Swirl-Clock Blind Falsifier v0.1.1

A standalone blind Python/C++ workbench for the **SC-II intrinsic modal phase
clock** hypothesis.

SC-II asks a different question than the earlier SC-I recurrent-shape clock:

> Does a vortex structure contain a robust, internally generated modal phase
> whose phase advances predictably over multiple wraps, even when the complete
> centerline does not return to the same shape every period?

See `SCII_PROTOCOL.md` for the preregistered mathematical definition and gates.

### v0.1.1 maintenance note

This release changes **reporting only**.  It does not change SC-II thresholds,
phase metrics, numerical physics, candidate selection, or mesh/provenance gates.
When no certified candidate exists, the final summary now preserves the Stage-A
coverage verdict and labels later stages explicitly as `NOT_REACHED`.

## Key design choices

- Reuses the proven C++/pybind11/OpenMP Biot-Savart kernel and numerical
  certification infrastructure from the v0.2.2.x modal workbench.
- Full-shape recurrence is **not** an SC-II requirement.
- Modes are learned only in an absolute early discovery window and then frozen.
- Primary phase is Hilbert/analytic-signal phase of a frozen POD coordinate.
- Only the natural baseline channel can produce an SC-II candidate.
- ±probe odd response remains diagnostic/null only.
- Requires >=4 wraps, monotone phase, low period CV, low phase diffusion,
  envelope persistence and out-of-sample phase prediction.
- Provisional candidates must survive low/high tangential mesh-gauge replay.
- Provenance robustness treats Fremlin shape variants as one source family.
- Stage B separately tests delayed stretch -> phase-velocity modulation and
  material-core specificity.
- Blind scoring never reads source identity.

## Fastest route: reuse an existing Stage-A run

If you already have a complete `outputs\basic` containing
`results_stage_a\candidates`, **do not recompute T=24**.

From this SC-II package run:

```bat
run_sc2_from_stage_a.cmd C:\path\to\old_package\outputs\basic
```

or, if the work directory is this package's own `outputs\basic`:

```bat
run_sc2_from_stage_a.cmd
```

The script performs:

1. SC-II Stage-A phase analysis on existing trajectories;
2. low mesh-gauge replay only for provisional SC-II candidates;
3. high mesh-gauge replay only for provisional candidates;
4. mesh-gauge certification;
5. blind provenance robustness;
6. material-core Stage B only for certified candidates;
7. fixed-core null;
8. causal phase-modulation analysis.

If Stage A produces zero provisional candidates, the expensive replay/Stage-B
branches automatically contain zero selected carriers.

## Full campaign

```bat
run_all.cmd --libraries=Fremlin,Gilbert,Katlas --min-carriers=2
```

Links only:

```bat
run_all.cmd --libraries=Gilbert,Katlas --min-carriers=2 --kind=links
```

Topology focus:

```bat
run_focus_topology.cmd 3_1 --libraries=Fremlin,Gilbert,Katlas --min-carriers=2 --kind=knots
```

The library/source machinery is inherited from the current modal workbench.
Katlas geometry is explicitly marked as generated geometry rather than published
source coordinates.

## Important outputs

```text
outputs\basic\analysis\blind_sc2_phase_modal_results.csv
outputs\basic\analysis\blind_sc2_carrier_summary.csv
outputs\basic\analysis\blind_sc2_stage_a_summary.json
outputs\basic\analysis\sc2_candidates_provisional.json
outputs\basic\analysis\blind_sc2_gauge_results.csv
outputs\basic\analysis\sc2_candidates.json
outputs\basic\analysis\blind_sc2_provenance_results.csv
outputs\basic\analysis\blind_sc2_provenance_summary.json
outputs\basic\analysis\blind_sc2_stage_b_results.csv
outputs\basic\analysis\blind_sc2_summary.json
outputs\basic\progress.log
```

## BASIC phase gates

The defaults are preregistered in `config/basic.json`:

```text
min phase wraps                         4
min monotone phase fraction            0.90
min phase linearity R^2                0.90
max cycle period CV                    0.15
max one-cycle phase diffusion RMS      0.75 rad
max envelope CV                        0.60
envelope retention range               0.40 .. 2.50
max prediction RMS                     1.00 rad
max terminal prediction error          1.57 rad
natural channel required               yes
```

These gates should not be changed after observing a carrier result.

## Existing-data regression used during development

The SC-II analyzer was run, without changing the preregistered thresholds, on
13 geometry-certified carriers from a prior 333-trajectory Stage-A campaign.
It produced zero provisional SC-II natural-channel candidates. The only mode
that passed both multi-wrap monotonicity and frequency-coherence was an odd
probe/control mode; it was rejected by independent SC-II gates and by the
mandatory natural-channel rule. This is a useful negative-control regression,
not a global SC-II falsification because the parent campaign had insufficient
geometry-valid coverage.

## Windows / MSVC

The native code uses `py::ssize_t`, never unqualified global `ssize_t`.
The `.cmd` focus launcher leaves option parsing to Python to avoid Windows batch
parsing problems with values such as `--libraries=Gilbert,Katlas`.

## Scientific scope

This workbench uses a regularized finite-core vortex-filament/Biot-Savart proxy.
A PASS establishes a candidate mechanism inside this numerical model, not a
proof for a full volumetric 3-D Euler system.
