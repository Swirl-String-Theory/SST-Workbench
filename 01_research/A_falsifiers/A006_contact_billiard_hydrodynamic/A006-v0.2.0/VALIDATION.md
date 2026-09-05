# Validation record — v0.2.0

Validation date: 2026-08-01  
Environment: Linux x86_64, Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, Matplotlib 3.10.8.

## Executed code checks

```text
python -m compileall -q sstcbhf scripts tests
python -m pytest -q
7 passed
```

The additional v0.2.0 test verifies that the bundled database is present, byte-sized as expected, has the declared SHA-256, and contains the `3:1:1` trefoil record with

```text
L = 16.371637
D = 1.0
Fourier coefficient count = 183
highest occupied mode = 250
```

Bundled database integrity:

```text
file     = data/ideal_favorites.txt
size     = 786423 bytes
SHA-256  = 942cb24b2a461b66cc3d35352f0723de97718a0e579ec524b8bb1c7ac4b9ad27
records  = 34
```

## Exact ring benchmark

The unit test `test_regularized_vortex_ring_is_relative_equilibrium` verifies a 32-point circular vortex ring at \(a/\Delta=0.2\):

```text
sampled thickness proxy             0.9984436342
relative-equilibrium residual       4.58e-16
Hamiltonian-gradient shape residual 5.56e-10
alignment cosine                    1.0000000000
tension CV                          3.99e-10
fitted scale                        1.40266188e-23 N
```

This is a code benchmark only. A circle is not a nontrivial knot and has a degenerate contact structure.

## Analytic torus-trefoil negative control

Executed:

```text
python -m sstcbhf demo --samples 128 --hydro-samples 32 \
  --out validation_outputs/demo_torus_trefoil
```

Result:

```text
scientific verdict: FALSIFIED_OR_UNRESOLVED_AT_ONE_OR_MORE_GATES
H0 PASS
H1 FAIL
H2 FAIL
H3 FAIL
H4 FAIL
H5 FAIL
H6 PASS
H7 FAIL
H8 FAIL
```

Selected diagnostics:

```text
contact inverse RMS                0.2188445547
contact orthogonality RMS          0.1250092298
branch-a period-9 closure          0.3345809972
branch-b period-9 closure          0.3345809806
paired orbit Hausdorff distance    0.1443945965
Carlen compatibility RMS           0.9629809538
inverse compatibility RMS          0.9601059191
local force-balance residual       0.1854307163
```

The negative control correctly fails the combined contact-map, inverse-map, paired-billiard and force-compatibility chain.

## Bundled Gilbert trefoil end-to-end smoke test

Executed:

```text
python -m sstcbhf analyze \
  --database data/ideal_favorites.txt --id 3:1:1 \
  --source-samples 4096 --samples 192 --hydro-samples 32 \
  --core-ratios 0.20 0.50 1.00 \
  --hydro-interactions full nonlocal \
  --out validation_outputs/bundled_gilbert_trefoil_smoke
```

Result:

```text
scientific verdict: FALSIFIED_OR_UNRESOLVED_AT_ONE_OR_MORE_GATES
H0 PASS
H1 PASS
H2 FAIL
H3 FAIL
H4 FAIL
H5 FAIL
H6 FAIL
H7 FAIL
H8 FAIL
```

Selected diagnostics:

```text
source length relative error       3.026349609e-4
source diameter relative error     7.454866181e-6
contact completeness               1.0000000000
contact inverse RMS                0.0755507328
contact orthogonality RMS          0.0509261723
branch-a period-9 closure          0.0013266535
branch-b period-9 closure          7.248216516e-8
paired orbit Hausdorff distance    0.0925286444
Carlen compatibility RMS           0.9841364292
inverse compatibility RMS          0.9294269181
local force-balance residual       0.5377421111
```

This low-resolution smoke test confirms that the full bundled database parses and that all output layers execute. It is not a convergence result. In particular, the small closure residual of one branch is insufficient: H3 also requires the inverse branch and paired orbitset to converge.

## RUN_ALL plan validation

Executed:

```text
python scripts/run_all_research.py \
  --preset max --plan-only --run-id validation_plan \
  --out-root validation_outputs/run_all_plan
```

Result:

```text
planned steps = 42
first step    = contact_convergence
last step     = hydro_invariance_rigid_transform
```

The generated plan includes the database audit, geometry/contact convergence, exclusion sweep, invariance/noise variants, negative controls, dense finite-core sweep, hydrodynamic resolution sweep, local-band sweep, physical-scale guard and hydrodynamic invariance tests.

## Not executed in the validation container

The complete `max` or `extreme` research matrix was not executed here. The reference Hamiltonian finite-difference gradient scales approximately as \(O(N^3)\), and a full matrix is intended for a long local SST-Workbench campaign. The included CMD runner writes a start marker and command line before each subprocess, streams output to both terminal and per-step logs, and resumes the newest incomplete run.

Validation artifacts are under:

```text
validation_outputs/pytest.log
validation_outputs/demo_torus_trefoil/
validation_outputs/bundled_gilbert_trefoil_smoke/
validation_outputs/run_all_plan/
```
