# Validation — E010 PKLSA v0.3.1

## Regression status

- Full pure-Python suite: **41 passed, 1 skipped, 0 failed**.
- C++/OpenMP Linux build: **compiled and imported successfully**.
- Full suite with native backend: **41 passed, 1 skipped, 0 failed**.
- Native exact kernels present: `writhe_acn_exact`, `linking_number_exact`.

The skipped test is the pre-existing optional historical PKLSA-v0.2.0 integration test when its external base package is not supplied.

## New literature-gate regression cases

The v0.3.1 tests include:

- exact polygonal Gauss linking on a synthetic Hopf link: \(|Lk|=1\) to floating-point precision;
- Cantarella writhe-convergence gate on a smooth \(T(2,3)\) torus trefoil;
- mirror reflection test showing simultaneous sign reversal of signed torsion integral and signed writhe;
- Oberti--Ricca analytic torus-knot length against direct high-resolution sampling;
- Przybyl--Pierański ideal-trefoil benchmark at the literature reference value.

## Bundled Gilbert ideal-trefoil fixture

The bundled `Ideal.txt.gz` `3_1` record has upstream diameter-convention reference

\[
L/D=16.371637,
\]

while the high-resolution Przybyl--Pierański target used by `B1` is

\[
L/D=16.3714672385.
\]

Their relative difference is

\[
1.04\times10^{-5},
\]

so the source reference itself is consistent with the literature benchmark.

For the PKLSA resolution ladder \(N=128,256,512,1024\), the hard gates give:

- `G1_isotopy_safe_sampling`: **PASS**;
- `G2_writhe_quadratic_convergence`: **PASS**, with estimated orders \(p=1.7366,1.8495\);
- `G3_signed_frenet_chirality_completeness`: **PASS**.

The contextual `B1_ideal_trefoil_ropelength` is intentionally a **soft FAIL**: the current numerical reach/doubly-critical-distance estimator gives a finest recomputed

\[
Rop=17.5702443767,
\]

about \(7.32\%\) above the literature value. This is retained as an explicit estimator-calibration issue. It does **not** invalidate the upstream Gilbert geometry reference and is not hidden by using the source-provided value as the recomputed result.

See `VALIDATION_V031.json` for machine-readable values and `docs/LITERATURE_GATES_V031.md` for gate definitions and references.
