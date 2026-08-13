# Validation — SST Hopf C++/pybind Benchmark Pack v0.1.3

## Scope

v0.1.3 is a numerical/certification patch driven by the first real STANDARD C++ outputs.

## Python/reference validation

**PASS**

- Python syntax compilation: PASS.
- Full STANDARD H0–H10 reference chain: 8/8 scripts exit 0.
- Step 3 exact seam tests: PASS.
- Step 4 N=64 regression: STANDARD_PASS.
- H5 constructed identity benchmark: IDENTITY_BENCHMARK_PASS.
- Director/Hodge convergence ladder tested through N=128.

## Key N=64 regression

User-supplied analytic benchmark:

```text
q_spinor                    0.951808376935...
old q_director (v0.1.2)     0.842922434799...
new q_director (v0.1.3)     0.979126949247...
delta_routes                0.027318572311...
delta_integer_director      0.020873050753...
delta_longitudinal          0.008132915985...
delta_div_projected         0.037244701313...
delta_curl_projected        0.039365210081...
H1                          STANDARD_PASS
H3                          STANDARD_PASS
```

The improved director value comes from the fourth-order director-curvature derivative plus explicit Hodge projection diagnostics. It is a numerical-method improvement, not new physical evidence.

## High-resolution reference result

For `N = 64, 96, 128`:

```text
N=64   q_spinor=0.95180838  q_director=0.97912695
N=96   q_spinor=0.97595057  q_director=0.99203506
N=128  q_spinor=0.98450021  q_director=0.99428719
```

At N=128:

```text
director reconstruction     CERTIFIED_PASS
joint H1                    STANDARD_PASS
H3                          STANDARD_PASS
overall                     STANDARD_PASS
```

The director reconstruction itself satisfies the strict v0.1.3 thresholds, but the direct spinor route still has about 1.55% integer error and therefore prevents a joint `CERTIFIED_PASS`. This is intentional and conservative.

## Seam regression

For the regularized `(m,n)=(1,1)` toroflux ansatz:

```text
delta_seam_director         ~2.45e-16
delta_seam_spinor_gauge     ~1.22e-16
```

The former `seam_diagnostic_99pct` is no longer treated as a seam certificate.

## H5 regression

With the constructed identity field:

```text
bridge_classification       IDENTITY_BENCHMARK_PASS
delta_omega                 ~2.995e-02
delta_helicity              ~8.961e-03
```

This does **not** close the independent SST bridge.

## Native C++ status in this environment

The new C++ fourth-order kernel was source-reviewed and added to the native parity test, but the current execution environment does not have the `pybind11` Python package/headers installed, so the v0.1.3 native extension was **not compiled here**.

The user's Windows workflow is the authoritative native test:

```cmd
RUN_ALL.cmd
RUN_DIRECTOR_CONVERGENCE.cmd
RUN_HIGHRES_HOPF.cmd
```

The package keeps the explicit build dependency contract:

```text
numpy>=2.0
pybind11>=2.13
setuptools>=68
wheel>=0.43
```
