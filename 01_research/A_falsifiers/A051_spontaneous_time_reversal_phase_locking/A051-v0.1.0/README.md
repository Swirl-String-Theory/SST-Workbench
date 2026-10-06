# A051 — SST Spontaneous Time-Reversal Phase-Locking Blind Falsifier v0.1.0

## Scientific question

Can an **unforced, time-reversal-symmetric** knotted finite-core dynamical system support two degenerate, stable phase-locked branches related by time reversal, with a nonzero time-odd internal order parameter?

The primary dimensionless two-mode observable is

\[
\chi_T(t)=\frac{2\,\mathrm{Im}[\eta_1^*(t)\eta_2(t)]}
{|\eta_1(t)|^2+|\eta_2(t)|^2+\varepsilon},\qquad -1\le \chi_T\le 1.
\]

It is invariant under a common phase gauge \(\eta_j\mapsto e^{i\theta}\eta_j\). In the default two-mode representation, the producer-supplied antiunitary time-reversal map must reduce to complex conjugation (or explicitly provide its representation map), giving \(\chi_T\mapsto-\chi_T\).

Phase locking is measured independently through

\[
Z_{12}=\frac{\sum_t w_t e^{i\phi_{12}(t)}}{\sum_t w_t},\qquad
R_{12}=|Z_{12}|,\qquad
\phi_{12}=\arg[\eta_2\eta_1^*],
\]

with amplitude weight

\[
w_t=\frac{2|\eta_1||\eta_2|}{|\eta_1|^2+|\eta_2|^2+\varepsilon}.
\]

A physical PASS requires **all** preregistered critical gates: independent phase observability, no time-odd forcing/bias, nonzero locked order, time-reversed partner antisymmetry, branch degeneracy, symmetry-neutral branch balance, numerical convergence, cross-geometry/source robustness, and producer-level reversibility certification. Missing prerequisites are `INDETERMINATE`, never forced to PASS/FAIL.

## Why this version is structured this way

The design explicitly incorporates upstream SST-Workbench results reviewed on 2026-10-02:

- **A045**: numerical/instrument gates pass, but `physics_verdict=UNTESTED`; formal Floquet is `SKIP_NO_CERTIFIED_RPO`. Therefore synthetic qualification is not physical evidence.
- **A048**: the independent Euler smoke is numerically clean, but the material-phase observable is not implemented and core resolution is unqualified. Therefore A051 refuses a physical branch verdict without an objective independent phase observable and resolved finite core.
- **A050**: temporal memory transfers, but real-geometry modal transfer is not reproduced. Therefore A051 requires cross-geometry/source robustness rather than a single embedding.
- **A038 / A031**: many numerical seed-qualification stages pass, but the long-window RPO remains indeterminate and no certified RPO is available. Therefore Floquet is optional and cannot be promoted without upstream certification.
- **A021**: trefoil self-confinement failed in the tested domain. A051 does not use self-confinement as evidence for phase locking.
- **A029 / A030**: propagation delay or geometric candidate phase is not equivalent to a physical material-phase lock. A051 keeps delay/holonomy diagnostics separate from the locking observable.

See `docs/UPSTREAM_EVIDENCE_2026-10-02.md` and `data/upstream_evidence_snapshot.json`.

## Status semantics

- `QUALIFIED_INSTRUMENT_ONLY`: synthetic reversible reference and evaluator logic pass; no SST physics claim.
- `INDETERMINATE_*`: physical input exists or upstream evidence is known, but one or more mandatory prerequisites are missing/unresolved.
- `FAIL_TESTED_DOMAIN`: at least one qualified physical critical gate fails.
- `SUPPORTED_TESTED_DOMAIN`: every mandatory physical gate passes for the preregistered tested population. This is not a general proof of SST.

## Workbench placement

```text
01_research/A_falsifiers/
  A051_spontaneous_time_reversal_phase_locking/
    FAMILY.yaml
    A051-v0.1.0/
```

`family_hierarchy.json` reviewed on 2026-10-02 declares `next_catalog_ids.A_falsifiers = A051`. The contemporaneous `catalog_index.json` is behind the physical tree (it does not yet contain A050), so this package ships **candidate additive patches** rather than overwriting registry files.

## Run

From `A051-v0.1.0` on Windows:

```cmd
run_all.cmd
```

Python reference only:

```cmd
run_python.cmd
```

Optional native build/parity:

```cmd
run_build_cpp.cmd
run_native_parity.cmd
```

Evaluate a producer dataset:

```cmd
python -m sst_trpl.cli physical --manifest path\to\manifest.json --output-dir outputs\physical
```

The input contract is documented in `docs/INPUT_CONTRACT.md`.

## Blindness

The blind evaluator contains no SST canonical constants, no expected phase, no preferred sign, and no target particle/knot identity. Producer/source identities can be anonymized. Reveal derives interpretation from immutable blind outputs; it does not recompute scientific metrics.
