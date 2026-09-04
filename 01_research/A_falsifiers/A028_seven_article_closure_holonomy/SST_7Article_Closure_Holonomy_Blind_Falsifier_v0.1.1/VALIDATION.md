# Validation and epistemic status

## Validation performed for v0.1.1

The package was syntax-checked and exercised end-to-end in the build environment.

### Python/C++ kernel selftest

`python scripts/selftest.py` returned `PASS`.

Checks included:

- closed-circle length against \(2\pi\);
- Python/C++17 curve-length parity;
- Hopf-link Gauss integral with \(|Lk|-1<3\times10^{-3}\);
- Python/C++17 Gauss-linking parity;
- integer phase winding \(W_\Phi=3\);
- periodic Taylor--Green incompressibility/pressure-Poisson closure;
- periodic Fourier Green reconstruction;
- exact even/odd observable decomposition.

Measured Taylor--Green results in this environment:

```text
pressure-Poisson relative residual = 2.2061401526383866e-14
periodic Green relative residual   = 5.6985437364457615e-03
native C++ kernel                  = active
OpenMP                             = active
```

The host had C++17/OpenMP and pybind11 headers available through another installed package, but did not have the standalone `pybind11` Python package and has no outbound package-network access.  Therefore the C++ source was compiled manually against the available headers for this validation.  On Windows, `run_00_install.cmd` installs the declared `pybind11` dependency and invokes the normal build path.

### End-to-end blind synthetic campaign

A synthetic case containing a closed centerline, integer phase field, periodic Taylor--Green Euler field, repeated time series, circulation-reversal pair, and equivalent representation pair was passed through:

```text
prepare_blind.py -> run_campaign.py -> freeze.sha256 -> reveal.py
```

The result was `PASS_WITH_AVAILABLE_GATES`.  Missing optional finite-size and commutator-refinement arrays correctly returned `INDETERMINATE` rather than being synthesized.

### Article-7 algebra guard

`run_cosmology_guard.cmd` / `scripts/audit_log_q_model.py` reproduces the independent joint-fit audit for the reviewed logarithmic model:

```text
q_infinity      = 0.1817586206896552
future_pole_z   = -0.29165752904763875
transition_z    = 1.5869608744177013
age_Gyr         = 14.829736298416817
regular(-1,0)   = false
```

These values are included as a methodological regression example, not as an SST cosmological law.

## What this package validates

- blind file handling and frozen thresholds;
- C++/Python geometric kernel parity;
- centerline-only Gauss-linking diagnostics without topology-layer promotion;
- phase winding and sampling-alias consistency;
- periodic pressure-Poisson and Green reconstruction;
- enstrophy/strain source ledger;
- repeatable or finite-size spectral diagnostics when time-series metadata are present;
- even/odd circulation-reversal decomposition;
- representation-invariance and optional commutator-refinement diagnostics.

## What it does not validate automatically

- that a KnotPlot/Ridgerunner centerline is an Euler solution;
- that a centerline hole contains material vorticity;
- that an internal phase field exists;
- that a phase singularity is a material vortex core;
- that an effective metric is fundamental spacetime curvature;
- that a good phenomenological fit derives SST dynamics.

An exit code zero means the software completed its preregistered checks.  It does not promote `REFERENCE_ONLY`, `INDETERMINATE`, research-track hypotheses, or conditional bridge assumptions into canon physics.

## v0.1.1 Windows/MSVC portability repair

The user-provided Visual Studio 2022 build log for v0.1.0 failed at the first
`ssize_t` declaration (`C4430`, `C2146`) and consequently produced an OpenMP loop
parse cascade. v0.1.1 removes every use of POSIX `ssize_t` from the C++ extension
and uses `std::ptrdiff_t`, a standard signed integral index type. The build helper
also verifies the extension import after build and can retry without OpenMP.
