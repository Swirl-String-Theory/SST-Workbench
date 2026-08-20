# Validation — SST Threaded-Hole Substrate Blind Falsifier v0.3.0

Validation below concerns software behavior and blind-protocol integrity only. It is not physical evidence for SST.

## Regression suite

```text
30 passed
```

The v0.3.0 additions explicitly test:

- Kelvin--M'Farlane analytic stagnation point, \(y_s/a=\sqrt{3}\);
- the non-trivial separatrix edge, \(x_{\rm edge}/a=2.087253791\ldots\);
- the removable \(X=0\) limit of the explicit \(\coth\) form without NaN/divide-by-zero warnings;
- the direct opposite-vortex co-moving stagnation velocity;
- geometry-only recovery of the central axis of a circular carrier;
- the dedicated `HOLE_ROBUSTNESS_COSTS` blind decision path;
- frozen regularized circular-ring regression: thick-core case -> `CAPTURED_ATMOSPHERE` with generic \(\chi_{\rm hole}>1\), thin-core case -> `OPEN_CHANNEL` with \(\chi_{\rm hole}<1\);
- all pre-existing v0.2.1 blind/seal, pressure, topology, contact, Windows UTF-8 and phase regressions.

## Analytic Kelvin oracle

The standalone oracle returned:

```text
status                                      PASS
stagnation_y_over_a_numeric                 1.7320508075688772
stagnation_abs_error                        0
separatrix_x_edge_over_a_numeric            2.087253791183074
separatrix_x_edge_abs_error                 1.83e-10
max_implicit_streamline_residual            4.44e-16
```

The oracle is run before the numerical campaign and its Kelvin reference values do not enter candidate scoring.

## Blind preparation qualification

The shipped basic preset produced:

```text
7 qualified carrier/thread strata
7 blind pairs
14 candidates
```

All seven requested basic carriers passed the preregistered source, hole-clearance, Gauss-link and exact finite segment-clearance gates.

The shipped extended preset produced:

```text
16 qualified carrier/thread strata
192 blind pairs
240 candidates
```

All 16 carrier/helix qualification strata passed. The extended pair count follows 8 carriers x 2 helix strata x 3 core-circulation strata x 4 nonzero beta strata.

## End-to-end blind/seal/reveal smoke

A reduced one-pair smoke run was executed with the NumPy reference backend and deliberately shortened streamline-path and finite-evolution horizons. The purpose was protocol validation, not physical inference.

```text
blind valid pairs                 1/1
blind decision basis              HOLE_ROBUSTNESS_COSTS
carrier identity read             false
condition identity read           false
seal verification                 PASS
```

The post-seal hole reveal executed successfully and kept legacy self-confinement inference empty for the `hole_only` decision mode, preventing the new gate from being misreported as a self-confinement result.

## Two-layer reveal guard

v0.3.0 reports two distinct statements:

1. **dynamical-hole existence** — whether a robust open channel or captured atmosphere survives finite evolution and perturbations;
2. **causal thread-circulation effect** — whether the active arm beats the identical visible zero-circulation control.

The causal carrier vote is mapped from the anonymous multi-cost winner sealed before identity reveal. The reveal does not select a favorable individual metric post hoc. A robust result in both active and null arms is therefore interpreted as carrier-generated/thread-independent hole dynamics, not evidence that thread circulation caused the hole.

## C++/pybind11 status

`cpp/native.cpp` is byte-identical to the validated v0.2.1 native kernel:

```text
sha256 a503092564f2632a42d6b938b81dfba216c97228904fabafed7f8f807bcdc4f9
```

The new Lagrangian tracer code calls the existing `field_velocity` interface, so a native build accelerates the new gate without adding a second unvalidated C++ kernel. The current packaging environment did not contain pybind11 headers, so the extension was not rebuilt here; `run_01_build_native.cmd` performs that build in the installed Windows virtual environment. The NumPy reference path was used for the v0.3.0 end-to-end smoke.

## Preset/config and source checks

- All 15 shipped JSON presets parse successfully.
- `python -m compileall` succeeds for source and tests.
- No control characters were found in source/config/document text files.
- No private identity is read by `workflow.run_blind` or `hole_transport`.
- The public manifest states the active/null visual-control semantics explicitly.

## Interpretation

Passing software validation establishes that the package asks the intended blinded question and preserves the active/null seal. It does not establish that a real incompressible Euler vortex knot possesses an invariant material separatrix. Any supportive filament result should be followed by volumetric Euler/VortexLab evolution and invariant-manifold extraction.
