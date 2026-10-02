# SST Chiral Kelvin Falsification Pack v0.1.0

C++/pybind11 + Python reference implementation for testing the
chiral-Kelvin-mode research direction.

## Epistemic scope

v0.1.0 is a **null-model and frozen-geometry falsification pack**.

It does NOT yet claim that the parametrized trefoil is a stationary
or relative-equilibrium SST vortex solution.

The torus trefoil is used to test symmetry, mirror transformations,
circulation reversal, the analytic Frechet derivative, and
chirality-resolved linear modes.

A later version must use the SST ideal-knot geometry and solve the
relative-equilibrium problem before the spectrum may be interpreted
as a physical stationary Kelvin spectrum.

## SST constants

```text
v_swirl    = 1.09384563e6 m s^-1
r_c        = 1.40897017e-15 m
rho_f      = 7.0e-7 kg m^-3
Gamma_0    = 2 pi r_c v_swirl
           ~= 9.6836192e-9 m^2 s^-1
```

## Implemented equations

Regularized finite-core Biot-Savart:

```text
V(q) =
Gamma/(4 pi)
integral
X'(q') x [X(q)-X(q')]
-------------------------------- dq'
(|X(q)-X(q')|^2+a^2)^(3/2)
```

Analytic Frechet action:

```text
delta V =
Gamma/(4 pi)
integral [

    xi'(q') x R / D^(3/2)

  + X'(q') x deltaR / D^(3/2)

  - 3 (R.deltaR)
      [X'(q') x R]
      / D^(5/2)

] dq'
```

Mode convention:

```text
L q_n = lambda_n q_n

lambda_n = sigma_n - i omega_n
```

Mode circularity:

```text
C_n =
2 Im sum(u_n* v_n)
------------------
sum(|u_n|^2+|v_n|^2)
```

with

```text
-1 <= C_n <= +1
```

## Hard falsification gates

### Frechet derivative

The analytic Jacobian action must reproduce a centered finite
difference of the nonlinear Biot-Savart operator.

### Circulation reversal

```text
V[X,-Gamma] = -V[X,+Gamma]
```

and therefore

```text
L(h,-s) = -L(h,s)
```

for the identical frozen geometry.

### Scalar energy

The minimal isotropic model predicts

```text
E(+,+)
=
E(+,-)
=
E(-,+)
=
E(-,-)
```

for exact mirror geometries and identical core models.

A violation is a FAIL until numerical/geometric asymmetry has been
excluded.

### Physical parity

For mirror matrix Q with det(Q)=-1:

```text
P : (h,s) -> (-h,-s)
```

The parity-related spectra must agree.

### Mode circularity

All eigenmodes must satisfy

```text
|C_n| <= 1
```

up to numerical roundoff.

## Build

Install:

```bash
python -m pip install numpy pybind11 setuptools
```

Build native:

```bash
python -m chiral_kelvin.build_ext_if_needed --force --strict
```

## Smoke runs

Ring:

```bash
python run_example.py --geometry ring --n 32 --force-build
```

Trefoil:

```bash
python run_example.py --geometry trefoil --n 32
```

Python-only reference:

```bash
python run_example.py --geometry trefoil --n 24 --force-python
```

## Sweep

```bash
python run_sweep.py ^
  --geometry trefoil ^
  --n-values 20,24,32 ^
  --core-factors 0.5,1.0,2.0 ^
  --out-json audit_out\sweep.json ^
  --out-csv audit_out\sweep.csv
```

## Full battery

```bash
python run_all_checks.py --out-dir audit_out --force-build
```

Expected output includes:

```text
audit_out/
    ring_N24.json
    ring_N24_modes.csv
    ring_N32.json
    ring_N32_modes.csv

    trefoil_N24.json
    trefoil_N24_modes.csv
    trefoil_N32.json
    trefoil_N32_modes.csv

    summary.csv
    audit_summary.json
```

## Interpretation

PASS means only:

1. the numerical implementation obeys the expected Euler/Biot-Savart
   null symmetries;
2. the analytic Jacobian agrees with finite differences;
3. the computed transverse modes possess well-defined bounded
   circularity;
4. no spurious four-state scalar energy splitting has appeared.

PASS is not evidence for SST.

The scientifically interesting next question is whether an
SST-specific finite-core or internal-swirl constitutive law produces
a reproducible residual after this null baseline has been passed.

## v0.2.0 target

The next version should add:

* loading of SST `ideal.txt` / `.fseries` / `.vect` centerlines;
* exact right/left mirror generation;
* arclength resampling;
* Bishop/parallel-transport frame;
* relative-equilibrium solve;
* rigid translation and rotation removal;
* tangent/gauge projection;
* sparse or matrix-free eigensolver;
* robust symmetry-based mode matching;
* four-state `(h,s)` campaign;
* Z2 x Z2 decomposition per matched mode;
* convergence and core-radius campaign.
