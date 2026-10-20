# F005 v0.4.1 — bounded family-review + independent development free-run

**Patch, not a full F005 instance. STATUS: DEVELOPMENT / NON-BLIND / NOT EULER / NOT PKLSA.**

## Why the original v0.4.0 run stopped

Observed in the supplied v0.4.0 report of 2026-10-19:

- `P5b`: `REVIEW_INCOMPLETE_PAIR_BUDGET`.
- Candidate pairs generated: 150,001; configured maximum: 150,000.
- Pairs actually scored: 0. Eight large buckets were skipped; upper bound of skipped pairs 133,892.
- `P6a`: `BLOCKED_FAMILY_AUDIT_INCOMPLETE`.
- `validation_free_run_metrics.csv`, `family_candidate_pairs_REVIEW.csv` and `fixed_validation_trace_sample.csv` contained **only CSV headers**.
- TEST/OOD output arrays were not read. No free-run performance measurement exists from this run.

This is a computational scheduling and coupling defect. **It is not a scientific FAIL**.

## Install (do not overwrite v0.4.0)

Copy this patch into the EXISTING F005 instance root:

`SST-Workbench/01_research/F_exploratory/F005_External_Wave_Benchmark/F005-v0.1.0/`

Keep `sources/`, `data/` previous scripts, and `outputs/` versions unchanged. Copy the `data/`, `tests/`, `docs/`, and `run_all_v041.cmd` paths from this ZIP.

## Run

```bat
py -3 -m pip install numpy matplotlib
run_all_v041.cmd
```

Or from PowerShell in F005 root: `./run_all_v041.cmd`.

The runner first executes 8 synthetic regressions and then the local full dataset pipeline. No 49.9-GB ZIP decompression, re-training, or test/OOD reveal is required.

## New review controls

1. Exact SHA-256 byte-duplicate audit over **input accelerations only**, all 9,822 trajectories. This scan is complete for finite inputs.
2. Fast 64/32/16-bin shape fingerprints; dense buckets are sampled rather than skipped.
3. Deterministic cap of **15,000 scored** approximate candidate pairs. **This is NOT exhaustive**, does not certify family independence, and is explicitly reported in the JSON.
4. Cross-partition examples go to `family_candidate_pairs_REVIEW.csv` for manual inspection.
5. Validating the frozen ARX(2) 0.1–3.0 s free-run uses only STANDARD_VALIDATION elevations (750 trajectories) with two initial observations per origin; future acceleration is an externally **known** input. This is *conditional*, not an autonomous excitation forecast.
6. TEST and OOD elevations are **not read**. No models are fit or hyperparameters tuned against validation in this patch.
7. An incomplete approximate family review **does not block** the explicitly noncertified development P6a run. Family certification remains blocked.

## Output location

`outputs/f005_free_run_family_v0.4.1/`

Files:

- `v041_report.json`: source hashes, P5b review, validation P6a results.
- `V041_SUMMARY.md`: status and per-horizon RMSE for ARX/persistence/linear.
- `validation_free_run_metrics.csv`: nonempty iff the development free-run ran.
- `family_candidate_pairs_REVIEW.csv`: sampled matched input pairs, not proven families.
- `fixed_validation_trace_sample.csv`: predeclared validation traces.
- `F005_FreeRun_Family_v0.4.1_DEVELOPMENT.pdf`: automated development-only PDF.

## Interpretation

**P5b:** `REVIEW_BOUNDED_SCREEN_NOT_FAMILY_CERTIFIED` even when there are zero detected near matches. Family ground truth from the source trajectory generator is needed for a group-disjoint, blind split. Sampled near matches are not a proof of leakage; missed near matches remain possible.

**P6a:** `DEVELOPMENT_CONDITIONAL_FREE_RUN_FAMILY_REVIEW_OPEN`. The validation result is useful for diagnostic comparison only. 4 ms one-step accuracy from v0.3 is not a substitute for 0.1–3 s errors.

**P7 / P8:** NOT RUN / UNRESOLVED. No physical SST inference.

## Requested returns

Send `v041_report.json`, `V041_SUMMARY.md`, and optionally `validation_free_run_metrics.csv` and the PDF. Do **not** upload the entire 50-GB dataset.

## References

```latex
\bibitem{Ljung1999}
L. Ljung, \emph{System Identification: Theory for the User}, 2nd ed.,
Prentice Hall (1999), ISBN 9780136566953.

\bibitem{Saffman1992}
P. G. Saffman, \emph{Vortex Dynamics}, Cambridge University Press (1992),
\url{https://doi.org/10.1017/CBO9780511624063}.
```
