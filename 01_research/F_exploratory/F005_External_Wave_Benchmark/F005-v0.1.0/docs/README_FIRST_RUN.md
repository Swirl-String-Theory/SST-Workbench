# F005-v0.4.0 - Free-Run Forecast & Independent Waveform-Family Audit

**Patch type:** additive DEVELOPMENT patch to existing `F005-v0.1.0/` workspace. It leaves the original instance, all prior outputs, and both large source ZIPs unchanged. **Not a frozen SST Framework instance, not blind certification, not Euler, not PKLSA.**

## Installation

Extract this PATCH ZIP **into the existing**:

```text
C:\workspace\projects\SST-Workbench\01_research\F_exploratory\F005_External_Wave_Benchmark\F005-v0.1.0\
```

Your v0.2.0 and v0.3.0 outputs must remain present. The local v0.3.0 `audit_report.json` is used as the **locked source for the ARX(2) coefficients**. The attached `evidence/audit_v0.3.0_reference.json` is an audit/reference snapshot only; it is **never substituted** for the local report. When existing input, split or metadata SHA-256 checks differ from the v0.3.0 report, the new runner **fails closed**.

Requires Python 3.10+, numpy, matplotlib (no scikit-learn, scipy, GPU, 50GB extraction, or network). Install if missing:

```powershell
py -3 -m pip install numpy matplotlib
```

## Run in the F005 root

```cmd
.\data\run_f005_v040.cmd
```

Or directly:

```powershell
py -3 .\data\f005_free_run_family_v0.4.0.py --root .
```

**Do not replace the existing `run_all.cmd`.** To integrate in the established main runner *after* v0.3.0, add this single line to your existing script (only after reviewing its orchestration):

```cmd
call data\run_f005_v040.cmd
```

## Outputs

```text
outputs/f005_free_run_family_v0.4.0/
  v040_report.json
  V040_SUMMARY.md
  validation_free_run_metrics.csv
  family_candidate_pairs_REVIEW.csv
  fixed_validation_trace_sample.csv
  F005_FreeRun_Family_v0.4.0_DEVELOPMENT.pdf
```

The user should return `v040_report.json` and `V040_SUMMARY.md` for scientific review; `validation_free_run_metrics.csv` and the PDF help with validation. No full raw dataset is necessary.

## P5b: independent input-waveform family review

**Inputs only**: scans all 9,822 acceleration trajectories, including held-out inputs for overlap auditing. NEVER examines held-out elevations. Builds three amplitude-normalized waveform hashes (64 bins/0.05, 32 bins/0.1, 16 bins/0.2), then checks candidate pairs under small time shifts (up to 4 samples). A candidate near-match must have Pearson correlation >= 0.995 and normalized RMSE <= 0.075. The candidate search is not exhaustive; oversized hash buckets are identified and reported as **unresolved**. A pair budget guard blocks the rollout stage if too many comparisons appear.

- Exact duplicates across partitions: objective input collision (unless publisher intentionally duplicated forcing).
- Coarse shape collisions: **heuristic only**; neither evidence of shared physical family nor proof of independence.
- Near matches: review flags. They are **not** publisher-defined trajectory-family IDs.
- No new train/validation/test split is made, and **the 750 TEST / 4,822 OOD output trajectories remain sealed**.

## P6a: conditionally autonomous rollouts

Uses the *frozen* v0.3.0 TRAIN fit:

```text
eta[n+1] = A*eta[n] + B*eta[n-1] + C*(dt**2)*a[n]
```

The v0.4.0 code reads no TEST/OOD water elevations. Only the 750 VALIDATION responses are indexed. Each rollout starts from exactly **two** measured elevations at predefined anchors near 0.004, 1.5 and 2.8 s; the subsequent elevations are **all generated recursively**. Known future commanded acceleration is provided to the model. It is a *conditional response forecast*, **not** a prediction of the future forcing.

Horizons: **0.1, 0.5, 1.0, 2.0, 3.0 s** (quantized to 4 ms). At each horizon report RMSE in SI meters for locked ARX(2), persistence, and linear trend extrapolation. Also record the maximum absolute forecast height; check against finite/physical ranges when reviewing. These are open-loop predictions conditional on two observed initial points, **not** repeated one-step teacher forcing.

Do not tune parameters or gate thresholds after looking at TEST/OOD data. Do not declare a physical mode frequency from the fitted ARX poles, nor a true family-separated split from these optical/signal-only tests.

## Safety / provenance

- The original 49.9 GB `DATASET.zip` is never opened; this patch uses only robot `INPUT_TRAIN.npy`, the VALIDATION indices of `OUTPUT_TRAIN.npy`, the original time vector and metadata.
- The full `OUTPUT_TRAIN.npy` is **not hashed**, deliberately: a whole-file hash would read sealed TEST/OOD response bytes. Only the selected VALIDATION response rows are fingerprinted for provenance.
- Neither train nor held-out outputs are used to refit the frozen model.
- The reference 0.3 output hashes, candidate split, and metadata must match. If not, the pipeline halts with a blocker rather than quietly refitting/reassigning splits.

## Regression tests

```powershell
py -3 -m unittest discover -s tests -p test_f005_v040.py -v
```

No real data values have been evaluated by the authoring environment; the bundled regressions use strictly synthetic signals. Local results must be reviewed before any physical interpretation.
