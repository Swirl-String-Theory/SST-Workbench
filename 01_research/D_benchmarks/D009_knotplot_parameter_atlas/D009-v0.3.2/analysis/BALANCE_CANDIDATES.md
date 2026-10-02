# Surrogate expansion/contraction balance candidates — Atlas v0.3.3

> **Candidate only.** This is not yet a proof that instantaneous `F_expand + F_contract = 0`.

Baseline:
- `charge = 15.0`
- `hooke = 1.0`
- `power = 5.0`
- `L ≈ 329.979215`
- `Rg ≈ 24.9477224`

Local one-factor response model:

\[\Delta L \approx 1.84984\,\Delta q -28.4986\,\Delta h -31.0409\,\Delta p\]

\[\Delta R_g \approx 0.0764612\,\Delta q -0.891066\,\Delta h -1.38528\,\Delta p\]

Solving both first-order cancellation conditions gives:

\[\Delta q \approx 22.2705t,\qquad \Delta h \approx 0.356366t,\qquad \Delta p=t.\]

## Recommended first joint candidate

\[\boxed{q\approx26.14,\quad hooke\approx1.178,\quad power\approx5.5}\]

This is the `t=0.5` point: deliberately close to the baseline so the local linear surrogate is least extrapolative.

## Candidate ladder

| t | charge | hooke | power |
|---:|---:|---:|---:|
| 0.25 | 20.5676 | 1.08909 | 5.25 |
| 0.50 | 26.1352 | 1.17818 | 5.5 |
| 0.75 | 31.7028 | 1.26727 | 5.75 |
| 1.00 | 37.2705 | 1.35637 | 6 |

## What must falsify/confirm it next

The next campaign must run these parameters **jointly**. A real restoring balance candidate requires a stable zero crossing of an expansion/contraction observable under perturbations around the candidate. Merely recovering the baseline endpoint length is insufficient.
