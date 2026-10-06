# A054 — Full-Factorial Skeleton × Twist-Knot × Polarity Blind Falsifier v0.1.1

## Research question

Can the strong `2+1` circulation-polarity effect observed in the sealed A054-v0.1.0 campaign survive a prospective, full-factorial test in which **collective skeleton**, **local twist-knot identity**, **component position**, **circulation polarity**, **circulation normalization**, and **PKLSA provider stratum** are varied independently?

This release is a **falsifier**, not a proton/neutron assignment procedure. It does not use nucleon masses, charge, atomic binding energies, Bohr radii, or SST canonical constants in blind scoring.

## Why v0.1.1 exists

The sealed v0.1.0 basic campaign showed two robust exploratory signals:

1. linked three-component skeletons strongly reduced the relative-equilibrium residual and increased cross-component stabilization relative to unlinked components;
2. for both linked analytic controls, the all-co-rotating sector had negative cross-stabilization while the three `2+1` sectors had positive cross-stabilization.

Those observations are frozen in `data/V010_DISCOVERY_PREREGISTRATION.json`, including the SHA-256 of the original v0.1.0 output archive. They are **discovery evidence only**. v0.1.1 does not import their numeric values into scoring thresholds.

## Full-factorial design

Three collective skeletons are used:

- `U`: mutually unlinked three-component control;
- `G`: analytic `T(3,3)` three-component torus-link / Triple-Gear proxy;
- `B`: analytic Borromean closed-braid skeleton.

For each PKLSA provider stratum, each component position independently receives either `5_2` or `6_1`. Therefore all

\[
2^3=8
\]

binary assignments are generated:

\[
000,001,010,011,100,101,110,111,
\]

where, **reveal-only**,

\[
0\equiv 5_2,
\qquad
1\equiv 6_1.
\]

This includes the historical mixed compositions

\[
5_2+5_2+6_1
\]

and

\[
5_2+6_1+6_1,
\]

all three position permutations of each, plus the homogeneous controls \(5_2^3\) and \(6_1^3\).

The geometry count is

\[
N_{\rm geom}=3+N_{\rm provider}\,(3)(8),
\]

where the first three are the analytic all-unknot skeleton controls. With the four provider-anchor pairs present in the v0.1.0 Workbench snapshot this becomes

\[
N_{\rm geom}=3+4\times24=99.
\]

The runtime E011 evidence graph remains authoritative; the package does not hard-code the provider count.

## Circulation / polarity factor

Every three-component geometry is evaluated under four relative circulation patterns modulo global reversal,

\[
(+++) ,\qquad (-++),\qquad (+-+),\qquad (++-),
\]

crossed with two normalization rules:

1. per-component quantum: \(|\Gamma_i|=1\);
2. fixed-total equal split: \(|\Gamma_i|=1/3\).

Thus each geometry has eight preregistered polarity sectors `Q0`--`Q7`.

The primary interaction observable remains

\[
S_{\times}=R_{\rm self}-R_{\rm full},
\]

where \(R\) is the rigid-translation/rotation relative-equilibrium residual. Positive \(S_{\times}\) means cross-component Biot--Savart interaction makes the three-component state more coherent under this operator.

For each one-opposed component position \(j\), v0.1.1 forms

\[
\Delta_j S_{\times}
=
S_{\times}^{(2+1,j)}-S_{\times}^{(+++)}.
\]

### Frozen prospective polarity gate

A geometry is tagged `polarity selection` only when, independently in **both** circulation normalizations:

\[
S_{\times}^{(+++) }\le 0,
\]

at least two of the three numerically/dynamically qualified `2+1` sectors satisfy

\[
S_{\times}^{(2+1,j)}>0,
\]

and the median `2+1` sector improves the relative-equilibrium residual:

\[
\operatorname{median}_j
\left(
R^{(+++) }-R^{(2+1,j)}
\right)>0.
\]

No numeric effect size from v0.1.0 is used as a threshold.

## PKLSA / E011 contract

Runtime geometry authority is:

- `E010-v0.3.1` for source geometry and exact loader/hash semantics;
- `E011-v0.3.0` for static-ready provider anchors and provider qualification.

Every `5_2` provider anchor is crossed with every `6_1` provider anchor. The current known state is:

- `5_2`: `CROSS_PROVIDER_ROBUST`;
- `6_1`: `CROSS_PROVIDER_SENSITIVE`.

Therefore a claim involving `6_1` must survive the full provider envelope or remain provider-conditional.

`L6a4` is **not** promoted to source-native Borromean evidence in this release. The Borromean geometry is an explicit generated analytic skeleton. Likewise, `G` is a `T(3,3)` topological proxy, not a mechanical tooth-contact model.

Decorated linked cases are constructed by local connected sum in sampled disjoint insertion balls. The constructor fails closed unless sampled clearance and pairwise skeleton-linking preservation are satisfied.

## Additional v0.1.1 diagnostics

### Mutual filament interaction energy

A target-free regularized mutual Hamiltonian proxy is evaluated from inter-component terms only,

\[
H_{\times}
=
\frac{1}{4\pi}
\sum_{i<j}\Gamma_i\Gamma_j
\oint_{C_i}\oint_{C_j}
\frac{d\boldsymbol\ell_i\cdot d\boldsymbol\ell_j}
{\sqrt{|\mathbf r_i-\mathbf r_j|^2+a^2}}.
\]

It is used only as a dimensionless comparative diagnostic.

For each component, a centre-of-mass-preserving relative displacement is applied and a finite-difference response is measured. v0.1.1 records the normalized first derivative and curvature; it **does not yet promote this diagnostic to a nucleon-stability PASS gate** because a full constrained Hessian/Kelvin--Floquet treatment remains downstream.

### Dynamic convergence repair

v0.1.0 used a fixed \(\Delta t\) and fixed step count at different spatial resolutions. v0.1.1 replaces that with

\[
\Delta t(N)
\propto N^{-2},
\qquad
T_{\rm final}=\text{constant}.
\]

The realized timestep is adjusted so every resolution reaches exactly the same final time. Spatial convergence now includes dynamic shape drift, linking drift and centroid-separation drift. `extended` additionally performs a factor-two temporal refinement at the finest spatial resolution.

## Backend qualification

The previous native/reference unit test could accidentally call the auto-selected native path for both sides. v0.1.1 separates

```text
induced_velocity_numpy(...)
induced_velocity_native(...)
```

and performs a deterministic independent comparison before scientific execution.

- `basic`: native preferred, NumPy allowed but explicitly reported;
- `extended`: C++17/pybind11/**OpenMP required**.

Backend qualification is written to `BACKEND_QUALIFICATION.json` and included in the blind seal.

## Status semantics

- `NUMERICALLY_QUALIFIED`: convergence/objectivity/backend checks passed. This is **not** a physical or particle PASS.
- `INCONCLUSIVE_NUMERICAL`: a numerical qualification gate failed. This is not a physical falsification.
- `QUALIFIED_SHORT_HORIZON`: one circulation sector passes the frozen short-horizon shape/link gates.
- `FAIL_SHORT_HORIZON`: that individual circulation sector exceeds a dynamical/topological short-horizon gate.
- `polarity.both_normalizations_gate = true`: the prospective sign/direction polarity criterion is satisfied in both normalizations.
- `PREPARED_PARTIAL_FAIL_CLOSED`: the full PKLSA factorial set was not available; no production nucleon conclusion may be claimed.

No weighted winner score is permitted.

## Reveal analyses

After the blind seal is frozen, reveal computes without rerunning physics:

1. matched skeleton contrasts `G-U`, `B-U`, `B-G` for every twist assignment/provider stratum;
2. every single-site `5_2 -> 6_1` substitution edge of the binary cube;
3. polarity benefit grouped by the **identity of the opposed component** (`5_2` versus `6_1`);
4. composition aggregates for \(5_2^3\), \(5_2^2 6_1\), \(5_2 6_1^2\), and \(6_1^3\);
5. provider envelopes and sign consistency.

This specifically tests whether the v0.1.0 `2+1` signal is a generic property of linked skeletons or depends on which twist knot carries the reversed circulation.

## Run

From `A054-v0.1.1`:

```cmd
run_all.cmd C:\workspace\projects\SST-Workbench
```

This performs install/build, self-tests, full blind preparation and the BASIC blind campaign, then **stops before reveal**.

For the stricter C++/OpenMP campaign:

```cmd
run_all_extended.cmd C:\workspace\projects\SST-Workbench
```

Freeze/package the blind output before reveal. The packer explicitly excludes `_private/PRIVATE_MAPPING.json`:

```cmd
run_90_pack_blind.cmd
```

Only after the blind report is frozen:

```cmd
run_99_reveal.cmd
```

## Expected output convention

```text
A054_Nucleon_Topology_Architecture_Blind_Falsifier_v0.1.1-outputs/
A054_Nucleon_Topology_Architecture_Blind_Falsifier_v0.1.1-outputs_BLIND.zip
A054_Nucleon_Topology_Architecture_Blind_Falsifier_v0.1.1-outputs_REVEALED.zip
```

## Scientific boundary

v0.1.1 tests a dimensionless finite-core vortex-filament architecture. It does **not** yet test:

- proton or neutron mass;
- electric charge;
- absolute SST energy normalization;
- atomic Coulomb/torsion closure;
- Bohr radius or atomic spectrum;
- exact per-component isotopy after decoration;
- full Kelvin eigenmodes, RPO recurrence or Floquet monodromy.

Those are later gates. A linked/polarity-selective candidate is not automatically a nucleon.

**Physical analogy:** think of three spinning loops like three coupled gears. v0.1.1 asks whether the coupling works because of the way the three loops are linked, because of the knot tied into each loop, or because one loop spins opposite to the other two.
