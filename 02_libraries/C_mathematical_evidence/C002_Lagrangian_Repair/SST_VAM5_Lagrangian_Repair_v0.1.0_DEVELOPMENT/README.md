# SST / VAM-5 Lagrangian Repair v0.1.0

**Status:** DEVELOPMENT / NOT PHYSICALLY CERTIFIED  
**Source:** historical 59-page VAM-5 PDF (10 July 2025), DOI 10.5281/zenodo.15772858.  
**Repair date:** 20 October 2026.

## Contents

- `SST_VAM5_Lagrangian_Repair_v0.1.0.pdf` — seven-page copy-ready scientific repair; includes corrected action, constraints, Hamiltonian, optional Euler-alpha model, failure map, independent measurement requirements and references.
- `SST_VAM5_Lagrangian_Repair_v0.1.0.tex` — full LaTeX source, standalone compilable with pdfLaTeX.
- `validate_repair.py` — reproducible SymPy + NumPy **identity/regression suite only**; no physical 3D knot simulation.
- `validation_report.json` — generated diagnostics and canonical constant calculations.
- `run_all.cmd` — one-click Windows run for algebraic regression and, optionally, PDF build if latexmk is installed.
- `requirements.txt`, `CHANGELOG.md`, `SHA256SUMS.txt`.

## Run (Windows)

```cmd
py -m pip install -r requirements.txt
run_all.cmd
```

Or platform-independent:

```bash
python -m pip install -r requirements.txt
python validate_repair.py
latexmk -pdf -interaction=nonstopmode -halt-on-error SST_VAM5_Lagrangian_Repair_v0.1.0.tex
```

## What is repaired

1. Constrained material-map action with Lagrange multiplier for `J=1`; Euler acceleration follows from a valid variation.
2. Momentum conjugate to the material position; constrained Hamiltonian on the `J=1` constraint surface.
3. A separate dimensionally correct `H^1` Euler-Poincare regularization with the **Euler limit** when `ell -> 0`.
4. Dimensional audit and explicit rejection of the old velocity-only canonical momentum, global phase gradient for vortical cores, nonvector electric field and unsupported gravitation/particle-mass identifications.

## What is not repaired or certified

The original complete PDF is not rewritten in place. There is no source-native PKLSA kernel, 3D Euler or Euler-alpha solver, proof of knot self-confinement, physical Swirl Clock, electron charge, quantized circulation, electromagnetism, gravity, GR compatibility or masses from this new formulation. The optional `ell = r_c` choice is a **hypothesis**, not an established core model.

**Validation:** 22/22 local checks PASS as of package creation. They are finite-grid and algebraic identity checks, not time-integration or experimental gates. The internal `G0/G1 PASS` labels are scoped to these checks only.

## Reproducibility boundary

This package does not modify the frozen SST Falsifier Framework, PKLSA, Google Drive or the historical VAM-5 preprint. The next scientific step is to integrate the Euler basis with an existing qualified PKLSA finite-core implementation, then apply strict independent time/space convergence and blind diagnostic gates.
