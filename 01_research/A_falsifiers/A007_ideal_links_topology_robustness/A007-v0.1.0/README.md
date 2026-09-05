# SST Ideal Links Comprehensive Test Suite v0.1.0

A self-contained campaign for the first ideal links through seven crossings:

`L2a1 L4a1 L5a1 L6a1 L6a2 L6a3 L6a4 L6a5 L6n1
L7a1 L7a2 L7a3 L7a4 L7a5 L7a6 L7a7 L7n1 L7n2`

The supplied `idealLinks.txt` actually contains 130 ideal links from 2–9 crossings. The CLI can
therefore run either the requested 18-link preregistered set or the complete database.

## Important normalization

Brian Gilbert's source uses diameter normalization \(D=1\). Its listed lengths are \(L/D\).
The standard mathematical ropelength uses tube radius \(\operatorname{Thi}=D/2\):

\[
\operatorname{Rop}_{\rm standard}=\frac{L}{D/2}=2\frac{L}{D}.
\]

The parser also uses the conventional Fourier constant term \(\mathbf A_0/2\).

## What is tested

1. XML/source integrity and target coverage.
2. Analytic Fourier reconstruction through the third derivative.
3. Length, curvature, torsion, bending, inertia, planarity and spectral tails.
4. Gauss-linking matrix, writhe proxy and transformation invariances.
5. Refined inter-component diameter contacts and nonlocal self-contact proxies.
6. Contact-graph cycle rank.
7. Every \(\pm\) circulation sector: 4 sectors for 2 components, 8 for 3 components.
8. Regularized Biot–Savart velocity, rigid-motion fit, relative-equilibrium residual, impulse and
   Neumann energy proxy.
9. Resolution and soft-core convergence.
10. Cross-link rankings, correlations, PCA and per-link JSON gate ledgers.
11. Optional SST canonical SI lift in the `max` preset; explicitly labelled Research Track.

## Install

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
py -3 -m pip install -e ".[test]"
py -3 -m pytest
```

## Run

Fast validation:

```powershell
py -3 scripts/run_all.py --preset quick
```

Full 18-link campaign:

```powershell
py -3 scripts/run_all.py --preset full
```

Maximum campaign:

```powershell
py -3 scripts/run_all.py --preset max
```

All 130 links in the database:

```powershell
py -3 scripts/run_all.py --preset full --all-database
```

Subset:

```powershell
py -3 scripts/run_all.py --preset full --ids L2a1 L6a4 L6n1 L7a7
```

Runs are resumable. Delete an individual `per_link/L*.json` file to recompute only that link, or
use `--no-resume`.

## Main outputs

- `summary.csv`
- `components.csv`
- `circulation_sign_configurations.csv`
- `mutual_contacts.csv`
- `convergence.csv`
- `REPORT.md`
- `run_metadata.json`
- `per_link/*.json`
- `plots/*.png`

## Scientific status

The Gauss-linking integer and source reconstruction are hard validation checks. Writhe,
contact-cycle rank, mirror ICP, regularized filament energy and relative-equilibrium scores are
diagnostics. They become SST predictions only after circulation, finite-core profile and closure
conditions are fixed independently.
