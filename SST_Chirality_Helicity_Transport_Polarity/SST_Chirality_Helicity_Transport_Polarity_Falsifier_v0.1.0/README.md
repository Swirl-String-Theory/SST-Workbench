# SST Chirality–Helicity Transport Polarity Falsifier v0.1.0

Blind C++17/pybind11 finite-core falsifier derived from the chirality–spin-polarity correspondence reported by Li *et al.* (2026), but formulated purely as an ideal-vortex dynamics test. It does **not** assume that CISS is hydrodynamic or that quantum spin equals vortex helicity.

## Primary falsification question

For a relaxed vortex-knot centerline `K` and its exact physical parity partner `P K`, does the finite-core linearized Biot–Savart operator generate a nonzero signed directional response whose sign reverses under parity?

The strongest target is

```text
Pi[P K] ≈ -Pi[K]       with       |Pi[P K]| ≈ |Pi[K]|,
```

while a 50/50 mirror pair cancels:

```text
(Pi[K] + Pi[P K])/2 ≈ 0.
```

A zero response is an informative null result, not a pass.

## Why the mirror generator reverses point order

A spatial reflection `R` has `det(R)=-1`. Velocity is polar but vorticity is axial:

```text
v'     = R v,
omega' = det(R) R omega.
```

For a filament represented by `omega ~ Gamma t`, merely reflecting the centerline would transform the polar tangent incorrectly for fixed `Gamma`. Therefore the code performs:

```text
x -> R x
point order -> reversed
```

so the parity partner is physical while `Gamma=+1` remains identical and hidden in both blind variants.

## Dynamics model

The regularized centerline field is

```text
v(x) = Gamma/(4 pi) sum_j [dl_j x (x-x_j+1/2)] / (|x-x_j+1/2|^2 + a^2)^(3/2).
```

Each closed curve is centered, uniformly resampled in arclength and normalized to total length `L=1`. The transverse finite-difference Jacobian of the regularized Biot–Savart map is built in a local `(n,b)` frame:

```text
du/dt = J u,
u = (delta_n, delta_b).
```

No helicity, writhe, knot label, mirror label or target sign enters `J`.

To make integration conditioning comparable across geometries, the code uses

```text
Jhat = J / Omega_J,
Omega_J = ||J||_F / sqrt(2N),
tau_J = Omega_J t.
```

For physical total centerline length `L_phys` and circulation `Gamma`, the physical Jacobian scale is proportional to `Gamma/L_phys^2`. With SST canonical

```text
Gamma_c = 2 pi r_c v_swirl = 9.683619203488876e-9 m^2 s^-1.
```

No physical length is imposed by the package because the KnotPlot/Ridgerunner input geometry is dimensionless.

## Directional transport observable

A localized parity-neutral real normal packet is initialized:

```text
delta_n(s,0) = exp[-d(s,s0)^2/(2 sigma^2)] cos[2 pi m (s-s0)],
delta_b(s,0) = 0.
```

For the evolved transverse field

```text
z(s,t) = delta_n(s,t) + i delta_b(s,t),
```

the signed spectral directional polarization is

```text
Pi(t) = [E(k>0)-E(k<0)]/[E(k>0)+E(k<0)].
```

The reported `transport_pi` is the mean late-time value averaged over the configured packet centers and carrier modes. Multiple symmetric packet centers are used to suppress accidental local-placement bias.

## Helicity diagnostic

The package separately reconstructs an untwisted Gaussian finite-core tube diagnostic

```text
omega(r) = Gamma/(pi a^2) exp(-r^2/a^2) t
```

and numerically integrates

```text
Xi_H = H/Gamma^2 = (1/Gamma^2) integral v . omega dV.
```

This is deliberately labeled `xi_helicity_tube`. It is **not** hard-coded as `Wr+Tw`; twist is not available from a bare centerline. Writhe is calculated independently with a discretized Gauss integral.

## Blind protocol

`prepare` creates an original/parity pair, randomly assigns them to `A/B`, writes only anonymous `.npy` inputs, and commits the hidden source/mirror mapping with SHA-256.

Blind dynamics explicitly reports:

```text
source_identity_read     = false
mirror_identity_read     = false
private_manifest_read    = false
carrier_identity_read    = false
condition_identity_read  = false
```

Source files are secretly shuffled before anonymous pair IDs are assigned, so `P0001`, `P0002`, ... do not encode filename order. The blind analyzer can test parity-oddness because `A` and `B` are known to be a matched pair, but it cannot know which is the source and which is the mirror. After blind analysis, `BLIND_SEAL.json` SHA-256-seals the manifest, results, analysis and report. `run_40_reveal.cmd` verifies both the blind seal and the private mapping commitment before attaching source names and roles. This is code-level/operational blinding; manually opening `_private/PRIVATE_MAPPING.json` would of course break the blind.

## Gates

For each pair and `(N,a/L)`:

```text
r_H  = |Xi_H,A + Xi_H,B| / (|Xi_H,A|+|Xi_H,B|)
r_Pi = |Pi_A   + Pi_B  | / (|Pi_A|  +|Pi_B|)
r_mag= ||Pi_A|-|Pi_B|| / (|Pi_A|+|Pi_B|)
```

Statuses:

- `INVALID_PARITY_HELICITY`: the constructed finite-core helicity itself fails its parity gate.
- `INVALID_PARITY_SPECTRUM`: parity partners do not have the same normalized linear spectrum within tolerance.
- `NULL_NO_DIRECTIONAL_SIGNAL`: parity is valid but `|Pi|` is below the predeclared signal floor.
- `INDETERMINATE_EXCITATION_SENSITIVE`: a signal exists but varies too strongly with packet location/mode.
- `PASS_MIRROR_ODD_TRANSPORT`: nonzero response, sign reversal and magnitude symmetry pass.
- `FAIL_MIRROR_ODD_TRANSPORT`: nonzero response exists but does not obey the required mirror relation.

The analyzer also reports anonymous Pearson/Spearman association between `Xi_H` and `Pi` and high-resolution convergence deltas.

## Dataset

Default:

```text
..\..\KnotPlot\knots\final
```

Supported coordinate inputs: `.txt`, `.xyz`, `.dat`, `.csv`, `.vect`, `.npy`. Text files must contain at least eight XYZ rows. KnotPlot binary `.k` files are intentionally not guessed/parsing-faked.

## One-click Windows runs

Basic, stops **before reveal**:

```bat
run_all.cmd
```

Extended certification:

```bat
run_all_extended.cmd
```

All parseable relaxed centerlines:

```bat
run_all_full.cmd
```

Each run creates a timestamped output directory and prints the exact reveal command. Inspect/save `REPORT_BLIND.md` first, then run e.g.

```bat
run_40_reveal.cmd outputs\basic_20260828_120000
```

Manual campaign:

```bat
run_campaign.cmd configs\basic.json outputs\my_test
```

## Output files

```text
BLIND_MANIFEST.json
prepare_errors.json
blind_inputs/*.npy
_private/PRIVATE_MAPPING.json
BLIND_RESULTS.json
ANALYSIS_BLIND.json
REPORT_BLIND.md
BLIND_SEAL.json
REVEALED_RESULTS.json       # only after reveal
REPORT_REVEALED.md          # only after reveal
```

## Numerical controls

- C++17 / pybind11 / OpenMP backend.
- MSVC-safe: uses `py::ssize_t`, never a global `ssize_t`.
- Arclength `ds_CV <= 0.20` pre-gate; resampling normally makes it much smaller.
- Central finite differences for `J`.
- RK4 with automatic subcycling from a normalized infinity-rate bound.
- Basic/extended/full configs use increasingly strict parity and convergence tolerances.
- `run_05_selftest.cmd` verifies writhe parity, finite-core helicity parity, the vector transformation of the Biot–Savart field, native Jacobian construction and finite RK4 transport.

## Interpretation limits

1. This v0.1.0 is a **linear finite-core filament-response falsifier**, not a full 3D Euler DNS.
2. The Gaussian tube helicity integral is a controlled reconstruction from the centerline; internal twist degrees of freedom are not present.
3. A nonzero `Pi` must survive resolution, core-radius and packet-placement variation before it is scientifically interesting.
4. A parity-odd `Pi` would demonstrate a chiral hydrodynamic transport channel in this model. It would not establish a quantum-mechanical CISS mechanism.
5. The strongest negative outcome is: helicity parity passes, numerical convergence passes, but `Pi -> 0` with increasing resolution. That directly falsifies the proposed directional channel for this operator/model class.

## References

See `REFERENCES.tex` for copy-ready `\\bibitem` entries.
