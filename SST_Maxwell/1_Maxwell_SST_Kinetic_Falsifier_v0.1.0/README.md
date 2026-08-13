# Maxwell–SST Kinetic Falsifier v0.1.0

A preregistered Python falsifier framework for the SST research track **“Maxwell–SST Kinetic Closure and Internal-Mode Thermodynamic Gate.”**

The package operationalizes four priorities:

1. **Internal-mode thermodynamic gate** — identify actually coupled modes, distinguish positive frequency from a true gap, apply accessibility/equilibration gates, and propagate declared discrete gaps into a partition-function heat-capacity audit.
2. **Kinetic closure** — ingest encounter-level mode-energy transfer and infer an empirical coupling proxy without assuming a hard-sphere or Maxwellian SST microphysics.
3. **Knot-ensemble stress** — compute the kinetic momentum-flux tensor separately from the canonical substrate Euler/Bernoulli scale.
4. **Orientation isotropization** — compute the second-rank orientation tensor `Q` and test ensemble isotropy independently of single-knot isotropy.

It also includes numerical-convergence, energy-ledger, spectroscopy and mode-taxonomy guards.

## What v0.1.0 does *not* do

It does **not** solve the Euler/Biot–Savart/finite-core dynamics, discover Kelvin modes from geometry, or derive a true quantum/discrete gap from first principles. Those quantities must come from a declared SST solver or experiment. v0.1.0 is the *audit/falsification layer* that prevents those outputs from being reinterpreted after the empirical target is known.

A result `NO_FALSIFIER_TRIGGERED_NOT_VALIDATION` means only that the supplied preregistered dataset did not trip a configured falsifier. It is not evidence that SST is correct.

## Install

From this directory:

```powershell
python -m pip install -e .[dev]
```

Or run directly without installation:

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m maxwell_sst_falsifier run --config examples\synthetic_fail\config.json --out outputs\synthetic_fail
```

## Windows shortcuts

- `run_tests.cmd` — run the unit tests.
- `run_demo_pass.cmd` — run the non-failing synthetic demonstration.
- `run_demo_fail.cmd` — run the intentionally failing synthetic demonstration.
- `run_campaign.cmd <config.json> <outdir>` — run a physical campaign.

## Required campaign inputs

The CSV filenames default to:

- `modes.csv`
- `amplitude_scan.csv`
- `encounters.csv`
- `convergence.csv`
- `spectroscopy.csv`
- `orientation.csv`
- `momenta.csv`
- `energy_ledger.csv`

Missing optional CSVs do not crash the run; the relevant gate becomes absent or indeterminate.

See `docs/DATA_SCHEMA.md` and `docs/PREREGISTRATION.md` before generating physical data.

## Core three-gate test

For each mode `a` of knot `K`, the campaign evaluates the operational counterpart of

```text
coupled  AND  drive energy >= gap  AND  equilibration time <= observation time.
```

In addition, thermal activation is checked against `Delta <= k_B T` when a positive discrete/activation gap has actually been declared.

## Critical gap guard

An amplitude–energy scan is fit near `A -> 0` as

`Delta E(A) ≈ intercept + slope * A^2`.

- intercept compatible with zero → `CONTINUOUS_TO_ZERO`;
- positive intercept → `FINITE_INTERCEPT_CANDIDATE`.

A finite numerical intercept is **not** automatically a quantum gap. It is only a candidate activation threshold until the admissible-state restriction is physically derived. Conversely, if a mode claims `gap_eV > 0` while its own small-amplitude branch tends continuously to zero, the package triggers the **Gap falsifier**.

## Output

Each run writes:

- `report.json` — machine-readable complete audit;
- `report.md` — human-readable summary.

## Synthetic examples

Both example datasets are explicitly marked `dataset_kind = synthetic`. Therefore the top-level verdict stays `DEMO_ONLY` even when internal test gates fail. This avoids accidental presentation of demo data as an SST result.
