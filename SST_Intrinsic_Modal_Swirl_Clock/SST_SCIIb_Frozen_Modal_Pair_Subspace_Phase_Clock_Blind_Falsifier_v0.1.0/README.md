# SST SC-IIb Frozen Modal-Pair / Subspace Phase-Clock Blind Falsifier v0.1.0

A standalone blind Python/C++ workbench for the next clock hypothesis suggested
by the SC-II result: a real internal travelling/rotating mode may occupy a
**two-dimensional near-degenerate modal subspace**, while either scalar POD
coordinate by itself has phase reversals or beating.

SC-IIb tests

\[
\phi_{ij}(t)=\operatorname{unwrap}\operatorname{atan2}(a_j(t),a_i(t))
\]

for discovery-frozen POD pairs.  It does **not** require full centerline
recurrence and it does not modify the closed-shape SC-I or scalar-phase SC-II
verdicts.

See `SCIIB_PROTOCOL.md` for the preregistered definition and gates.

## Fastest first run — reuse your existing Stage-A data

Your expensive T=24 trajectories can be reused directly:

```bat
run_sciib_from_stage_a.cmd C:\path\to\SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v0.2.2.5\outputs\basic
```

No nominal Stage-A Biot-Savart integration is recomputed.  The script performs:

1. blind discovery-only modal-pair selection and holdout phase analysis;
2. low mesh-gauge replay only for provisional SC-IIb carriers;
3. high mesh-gauge replay;
4. frozen-subspace mesh-gauge certification;
5. source-family-balanced provenance analysis;
6. material-core Stage B only for certified candidates;
7. fixed-core mechanism null;
8. phase-tangent stretch -> phase-velocity causal analysis.

If Stage A returns zero provisional candidates, the expensive replay and Stage-B
branches select zero carriers.

## Full campaign

```bat
run_all.cmd --libraries=Fremlin,Gilbert,Katlas --min-carriers=2 --kind=knots
```

Links only:

```bat
run_links.cmd
```

One topology:

```bat
run_focus_topology.cmd 3_1 --libraries=Fremlin,Gilbert,Katlas --min-carriers=2 --kind=knots
```

Hopf link:

```bat
run_focus_topology.cmd L2a1 --libraries=Gilbert,Katlas --min-carriers=2 --kind=links
```

The focus launcher leaves `--libraries=Gilbert,Katlas` parsing to Python, not
Windows batch parsing.

## BASIC primary gates

### Q1 discovery pair

```text
combined discovery energy       >= 0.05
energy balance                  >= 0.35
pair circularity                >= 0.80
discovery frequency split       <= 0.20
quadrature PLV                  >= 0.60
quadrature error                <= 0.55 rad
discovery rotation sign         >= 0.80
```

### Q2–Q7 holdout/certification

```text
phase wraps                     >= 4
monotone phase fraction         >= 0.90
modal angular-momentum sign     >= 0.90
phase-linearity R^2             >= 0.90
cycle period CV                 <= 0.15
instantaneous omega CV          <= 0.50
one-cycle phase diffusion RMS   <= 0.75 rad
pair-radius CV                  <= 0.60
radius retention                0.40 .. 2.50
reliable-radius fraction        >= 0.95
phase prediction RMS            <= 1.00 rad
terminal phase prediction       <= 1.57 rad
basis-gauge frequency spread    <= 1e-6
natural channel                 required
```

Thresholds are in the config JSON and are not to be loosened after observing a
carrier.

## Why the pair gate is different from SC-II

SC-II uses a scalar analytic signal.  SC-IIb instead asks whether the trajectory
actually rotates in a frozen plane:

\[
L_{ij}=a_i\dot a_j-a_j\dot a_i.
\]

A good clock therefore has a persistent sign of `L_ij`, a stable radius away
from the origin, low phase diffusion, and predictable phase velocity.

The subspace is explicitly re-expressed under rotations/sign flips/swaps of the
POD basis.  A claimed frequency that changes under those coordinate choices is
rejected.

## Important outputs

```text
analysis\blind_sciib_pair_modal_results.csv
analysis\blind_sciib_carrier_summary.csv
analysis\blind_sciib_stage_a_summary.json
analysis\sciib_candidates_provisional.json
analysis\blind_sciib_gauge_results.csv
analysis\sciib_candidates.json
analysis\blind_sciib_provenance_results.csv
analysis\blind_sciib_provenance_summary.json
analysis\blind_sciib_stage_b_results.csv
analysis\blind_sciib_summary.json
```

## Development regression on the existing baseline

The gates were frozen before running the new pair analysis on the previous
333-trajectory campaign.  For a runtime-efficient primary-channel regression,
only the 13 already geometry-certified carriers were materialized and only the
natural channel was analyzed.  There were 273 natural mode-pair hypotheses:

```text
Q1 discovery-eligible pairs          2
Q2 directed multi-wrap rotations     1
Q3 frequency-coherent pairs          0
Q4 phase/radius-stable pairs          0
Q5 predictive pairs                  0
provisional SC-IIb candidates        0
```

The correct global verdict remains
`INDETERMINATE_SCIIB_INSUFFICIENT_VALID_COVERAGE` because only 13/111 parent
carriers were geometry-certified.  See `REAL_DATA_REGRESSION.json`.

## Numerical implementation

- Python + NumPy analysis;
- C++/pybind11/OpenMP regularized Biot-Savart kernel;
- per-component geometry support for links;
- inherited mesh certification and source-provenance machinery;
- `py::ssize_t` only in the native extension; no global unqualified `ssize_t`.

The native physics kernel is byte-identical to the inherited v0.2.2.8/SC-II
kernel.  SC-IIb changes the observable and falsification logic, not the vortex
physics.
