# Validation and epistemic status

## Validation performed for v0.1.2

The v0.1.2 release was syntax-checked and exercised against both synthetic cases and the 49-case prepared output set from the uploaded v0.1.1 campaign.

### Python selftest

`python scripts/selftest.py` returned `PASS`.

Checks included:

- closed-circle length against \(2\pi\);
- Hopf-link Gauss integral with \(|Lk|-1<3\times10^{-3}\);
- integer phase winding \(W_\Phi=3\);
- periodic Taylor--Green incompressibility/pressure-Poisson closure;
- periodic Fourier Green reconstruction;
- exact even/odd observable decomposition;
- explicit blank-line multi-component TXT parsing;
- validated jump-fallback parsing;
- false-split rejection for a corrupted/open single sequence.

Measured Taylor--Green results in this build environment:

```text
pressure-Poisson relative residual = 2.2061401526383866e-14
periodic Green relative residual   = 5.6985437364457615e-03
```

The current container does not have the standalone `pybind11` package and has no outbound package network, so the v0.1.2 Linux validation used the Python fallback. The C++17 source retains the v0.1.1 `std::ptrdiff_t` MSVC portability correction; Windows `run_00_install.cmd` installs `pybind11`, builds the native extension, and runs the same parity selftest before any campaign.

### Blind-infrastructure selftest

`python scripts/selftest_blind.py` returned `PASS`.

It verifies that two preparations of one unchanged dataset, using the shared blind state, receive identical:

```text
case IDs
train/holdout assignments
component counts
dataset snapshot SHA-256
```

It also runs a blind campaign, hashes the **actual saved bytes** of `opaque_results.json`, verifies that `freeze.sha256` matches them, and confirms that reveal refuses unverified data and succeeds only after freeze/private-commitment verification.

### v0.1.1 49-case prepared-data regression

The uploaded v0.1.1 results were reconstructed into a regression dataset preserving the legacy concatenated point order. v0.1.2 then parsed and scored all 49 cases in EXTENDED mode.

Results:

```text
parser component-count mismatches = 0 / 49
G00 geometry input                 = 49 / 49 PASS
G01 resolution convergence         = 49 / 49 PASS
multi-component G03 cases          = 24
max G03 integer residual @1024     = 0.0028357249955792696
G03 numerical integer consistency = 24 / 24 true
max corrected closure ratio        = 0.006062539786008194
```

The same reconstructed 49-case snapshot was separately prepared in BASIC and EXTENDED mode with one shared blind state. `scripts/compare_manifests.py` confirmed all 49 opaque IDs, train/holdout labels, and component counts matched exactly.

The previous Gauss-midpoint audit gave the following worst integer residuals for the high-linking set:

```text
native/original sampling : 0.0316741034
512-point resampling     : 0.0113676500
1024-point resampling    : 0.0028357250
```

Therefore G03 uses 512 points in BASIC and 1024 in EXTENDED. G03 remains `REFERENCE_ONLY`.

### Article-7 algebra guard

`run_cosmology_guard.cmd` / `scripts/audit_log_q_model.py` remains a methodological regression example for the reviewed logarithmic cosmology ansatz. It is not promoted to SST cosmology.

## What this package validates

- blind file handling and frozen thresholds;
- byte-stable SHA-256 commitments on saved files;
- reusable blind identity/split for the same dataset snapshot;
- closed-component recovery from supported text/VECT inputs;
- centerline-only Gauss-linking diagnostics without topology-layer promotion;
- phase winding and sampling-alias consistency when phase data exist;
- periodic pressure-Poisson and Green reconstruction when volume fields exist;
- enstrophy/strain pressure-source ledger;
- repeated or finite-size spectral diagnostics when time-series metadata exist;
- even/odd circulation-reversal decomposition;
- representation-invariance and optional commutator-refinement diagnostics.

## What it does not validate automatically

- that a KnotPlot/Ridgerunner centerline is an Euler solution;
- that a centerline hole contains material vorticity;
- that an internal phase field exists;
- that a phase singularity is a material vortex core;
- that pairwise \(Lk=0\) makes a multicomponent link globally trivial;
- that an effective metric is fundamental spacetime curvature;
- that a good phenomenological fit derives SST dynamics.

An exit code zero means the software completed its preregistered checks. It does not promote `REFERENCE_ONLY`, `INDETERMINATE`, research-track hypotheses, or conditional bridge assumptions into canon physics.

## Historical Windows/MSVC repair retained from v0.1.1

The user-provided Visual Studio 2022 v0.1.0 build failed at POSIX `ssize_t`, producing the subsequent OpenMP parse cascade. v0.1.1 replaced that index with standard C++17 `std::ptrdiff_t`; v0.1.2 retains this fix unchanged and retains the OpenMP-to-serial fallback build policy.
