# Validation record — v0.1.0

Validation date: 2026-08-01  
Environment: Linux x86_64, Python 3.13, NumPy/SciPy/Matplotlib from the active runtime.

## Executed checks

```text
python -m compileall -q sstcbhf scripts tests
python -m pytest -q
6 passed

python -m pip install -e . --no-deps --no-build-isolation
python -m sstcbhf --help
sst-cbhf --help
```

The editable install succeeded with build isolation disabled. This is also how the
Windows BAT files install the local package, preventing an unnecessary online build
dependency lookup.

## Exact ring benchmark

The unit test `test_regularized_vortex_ring_is_relative_equilibrium` verifies a
32-point circular vortex ring at \(a/\Delta=0.2\):

```text
sampled thickness proxy             0.9984436342
relative-equilibrium residual       4.58e-16
Hamiltonian-gradient shape residual 5.56e-10
alignment cosine                    1.0000000000
tension CV                          3.99e-10
fitted scale                        1.40266188e-23 N
```

This is a code benchmark only. A circle is not a nontrivial knot and has a degenerate
contact set.

## Analytic torus-trefoil negative control

Executed:

```text
python -m sstcbhf demo \
  --samples 192 \
  --hydro-samples 64 \
  --thresholds-json configs/default_thresholds.json \
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
length                              31.8868723312
sampled thickness proxy              0.8333409565
sampled L/(2 Delta)                 19.1319483833
contact inverse RMS                  0.1894375653
contact orthogonality RMS            0.1271413361
branch-a period-9 closure             1.0863e-05
branch-b period-9 closure             1.3137e-02
paired orbit Hausdorff distance       5.4999e-02
Carlen compatibility RMS              0.9816307529
inverse compatibility RMS             0.9807980775
```

This negative control is important: one contact branch alone can exhibit a small
period-9 residual even for a non-ideal torus trefoil. H3 therefore requires both inverse
branches to close and to generate the same orbitset. The complete gate conjunction,
not the number nine alone, is the falsification object.

## Negative-control convergence ladder

Executed at \(N=64,96,128,192\). The contact inverse RMS remained approximately
\(0.19\)–\(0.23\), and the paired period-9 orbit Hausdorff residual did not converge to
zero. This correctly blocks promotion of the negative control.

Outputs are archived in:

```text
validation_outputs/demo_torus_trefoil/
validation_outputs/convergence_torus_trefoil/
```

## Not executed in this build environment

The full Brian Gilbert `3:1:1` campaign was not run because the user-owned
`ideal_favorites.txt` is intentionally not copied into this archive. The package parser
and mini-database fixture were tested. Place the original database under
`data/ideal_favorites.txt` and run `RUN_GILBERT_TREFOIL.bat` locally.

No claim is made that the current sampled contact solver reproduces Carlens biarc
contact map before that real-data and Ridgerunner convergence campaign is completed.
