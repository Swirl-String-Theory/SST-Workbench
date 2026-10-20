# A003 Fourier Knot Import Adapter v0.2.3

**Target atlas:** adjacent `../A003-v0.1.2` (384 source XYZ; 48 seeds). Pinned original manifest SHA-256 unchanged.

## Reason for hotfix

G5 reports from v0.2.2 identified `pyknotid==0.5.3` with `numpy==2.4.6` failing because its code references removed `np.float`. Another report returned `No module named 'pyknotid'` from a different interpreter context. This patch fixes only the first compatibility issue; check which Python environment executes the second.

The shim temporarily maps missing `np.float`, `np.int`, `np.complex` to Python builtin scalar types *only while importing/running pyknotid*. It removes only its own assignments in a `finally` block. This scoped process-global compatibility mechanism assumes **single-threaded execution**. It does not edit NumPy, site-packages or source XYZ bytes on disk.

## Installation

Unzip as an independent sibling folder:

```text
A003_Fourier_Knot_Seed_Atlas/
  A003-v0.1.2/
  A003_Fourier_Knot_Import_Adapter_v0.2.2/  (untouched)
  A003_Fourier_Knot_Import_Adapter_v0.2.3/  (new)
```

Open CMD with the Workbench `.venv` activated and run:

```bat
python -c "import sys, numpy, pyknotid; print(sys.executable); print(numpy.__version__); print(pyknotid.__file__)"
run_all.cmd
run_g5_smoke.cmd
run_g5_fibonacci_torus.cmd
```

`run_g5_fibonacci_torus.cmd` checks six Fibonacci-torus seeds at 1200 and 2400 points. The slower non-Cython provider can be expensive at high crossing complexity. A nonzero exit code means **not qualified**; inspect `outputs_g5_fibonacci_torus/validation_report.json` and each `seed_results[*].error`. Do not use `run_g5.cmd` for all 48 seeds before the small screen passes.

To run a diagnostic that does not enforce G5 evidence:

```bat
python fourier_atlas_adapter.py --reference-core-radius-units 0.05 --g5 --g5-family fibonacci_torus --g5-resolutions BASIC catalog
```

**Gate semantics:** G0–G3 geometric validation; G4 assumed physical scale `a_star=0.05` in source units mapped to `r_c=1.40897017e-15 m`; G5 determinant checks are necessary but not sufficient for knot equivalence and cannot certify chirality; G6 Euler/PKLSA is unexecuted. Never promote the source `topology_status` based on determinant alone.

## Regressions / attestation

`python -m unittest discover -s tests -v` runs source-integrity, frozen manifest, sampling, mirror and temporary-alias regression tests. This deliverable has been tested under NumPy 2.3.5 against a simulated `pyknotid` determinant call; the real provider is unavailable in the artifact environment. The actual G5 result on the Windows environment must be read from its run report.

`run_g5_smoke.cmd` is a short, isolated software check on a synthetic analytic trefoil using 240 points. It requires determinant 3 and reports an exception if pyknotid still fails; it does **not** certify the trefoil topology. G5 remains `NOT_RUN` until a separate screen is executed.
