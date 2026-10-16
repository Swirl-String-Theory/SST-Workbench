# SST Triadic–Casimir / PKLSA Blind Falsifier v0.2.0

**Validated status:** 17 portable regression tests; three independent tamper-evident dataset seals; geometry-only `3_1` PKLSA/KnotPlot production-lineage source; always-on PDF from Python standard library. **No qualified physical SST-Casimir force.**

## Repair of the v0.1.0 missing-PDF problem

The previous package included a precompiled PDF but `run_all.cmd` never regenerated one. The old LaTeX script required `pdflatex`, often absent on Windows. This version fixes the execution path: `run_all.cmd` invokes `triadic.entrypoint`, which produces a **new PDF after every BLIND, ALL, FULL, BASIC, FRAMEWORK or REVEAL run**. The renderer uses **Python 3.10+ standard library only**, with no TeX, ReportLab, internet or other dependency. It explicitly reports the exact generated and published paths.

On Windows:

```bat
run_all.cmd
run_all.cmd FRAMEWORK
run_all.cmd PKLSA
run_all.cmd VERIFY
run_all.cmd SELFTEST
run_all.cmd REPORT
run_all.cmd REVEAL
```

`ALL` is the default. It runs the portable control pilot **without revealing the private comparator**, attempts the **actual frozen** SST framework v1.0.7 if installed, and publishes the PDF even if the official framework is unavailable (with truthful `FRAMEWORK_NOT_FOUND` status). `FRAMEWORK` explicitly requires the official framework and fails with a nonzero exit status if it cannot run. `FULL` has the same strict framework requirement. `BASIC` also attempts the framework but remains a portable diagnostic. `CERTIFY` remains fail-closed until physical providers and dynamics meet the certification contract.

**PDF outputs on the local machine:**

```text
<extract-dir>\Triadic_Casimir_Framework_PKLSA_v0.2.0\reports\TRIADIC_CASIMIR_v0.2.0_FALSIFIER_REPORT.pdf
<extract-dir>\Triadic_Casimir_Framework_PKLSA_v0.2.0_FALSIFIER_REPORT.pdf
```

On Linux: `./run_all.sh ALL`. The copied PDF is deliberately next to the version directory, consistent with the SST Workbench output convention.

## Using the genuine v1.0.7 canonical framework

The package does **not** modify or counterfeit the frozen framework. When you run `run_all.cmd FRAMEWORK`, the adapter searches for:

```text
C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.7
```

or uses an explicitly configured environment variable:

```bat
set SST_FALSIFIER_FRAMEWORK_ROOT=C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.7
run_all.cmd FRAMEWORK
```

The framework root must contain `CANONICAL_FREEZE.json` with `version: 1.0.7` and `status: CANONICAL_FROZEN` plus its genuine generator and package. The adapter runs **the original `tools/new_falsifier.py`** to create `FRAMEWORK_INSTANCE\TCAS-v0.2.0`, copies only the scientific experiment into that instance, and invokes its original `run_instance.py` with `FREEZE`, `FULL`, `REVEAL_IF_ALLOWED` (the latter will be withheld while physical G3 is `UNRESOLVED`). In the generated instance, the canonical gate ledger, immutable preregistration bundle, source inventory, blind ZIP and official report attempt are managed by v1.0.7. No local reimplementation is represented as a framework certification.

The `minimal` frozen framework profile runs a Python reference, *not* CPU-native or GPU strict certification. The already separate standalone C++ numerical parity script is not promoted to official C++ backend certification. `FRAMEWORK_INSTANCE` is never written into the canonical template directory. The first generation freezes an immutable campaign; if the scientific protocol changes, create a new version rather than editing a frozen instance.

Inspect `FRAMEWORK_STATUS.json`, `reports/FRAMEWORK_RUN.log` and `FRAMEWORK_INSTANCE/TCAS-v0.2.0/Triadic_Casimir_v0.2.0-outputs/GATE_LEDGER.json` after the run.

## Three independently sealed datasets (new v0.2.0 campaign)

- **D01_EULER**: the original analytical incompressible flows **plus** actual sourced `N300` trefoil geometry and metadata from the KnotPlot/PKLSA input lineage; regularized Biot–Savart velocity, strain/vorticity and pressure-Poisson-source diagnostics. The trefoil provider is singular and geometry-only.
- **D02_CLOCK_LINK**: gauge phase/holonomy and positive-frequency one-body toy oscillator controls.
- **D03_TWO_SURFACE**: held-out distances and two-body toy scalar-surface thermodynamics/force checks.

Each dataset retains its independent `seals/Dxx.seal.json`. The global commitment binds all three root hashes and the comparator's SHA-256. D01 **has a new seal** because real source bytes have been added; D02/D03 can retain their previous content hashes. None of the individual dataset seals is a cryptographic third-party signature; publish the distribution SHA-256 externally for version authenticity. The comparator is included but not read by the BLIND kernel.

## Real PKLSA source and qualification limitations

Source: [`knot_3.1_trial_002k_rr_010k_coarse_rr_050k_eqfinal_rr_020k_polish_uniform_N300.txt`](https://drive.google.com/file/d/1iOeQe6-jHcBk_NYNwZe3e-N2DQPwohmI/view), 300 point trefoil centerline, sourced from the existing KnotPlot relaxed production lineage. Its raw SHA-256 and upstream Drive ID are recorded in `data/D01_EULER/pklsa/source.json` and verified on every run.

This is **not** a source with time-dependent Euler trajectories, wall pressure conditions, independent second upstream provider or atom–link current coupling. The E010 production atlas contains a same-family carrier record, but it is **not** assumed byte-identical to this selected N300 polished export. Geometry subsampling at 75/150/300 points is numerical convergence, not cross-provider replication.

Run `run_all.cmd PKLSA` to print the explicit geometry/field diagnostics; `run_all.cmd ALL` includes them in D01's sealed analysis and dynamic PDF.

## Source and scientific controls

The model intentionally has two *independent* theoretical branches: Euler geometry/pressure and the separately postulated canon link sector. D01/D02 pass implementation controls but do not determine the physical coefficient `rho_eff`, the quantum fluctuation normalization, an electromagnetic surface reflectivity, or an absolute Casimir amplitude. D03 attraction is a positive-stiffness **classical thermal scalar toy**, not a predicted force between metallic plates.

Source/research trace: SST Canon v0.8.36 §§3.5, 3.10, 7.1, 11.16–11.17, S.2, S.52; A046 v0.2.0/v0.3.0; E010 PKLSA production atlas v0.3.1. All numerical similarity parameters are identified as model or discretization assumptions.

## Required future scientific gates

Independent second PKLSA production source; dynamic Euler temporal phase/pressure solutions; physically certified metal boundary condition; atom–link microscopic source coupling; independently determined fluctuation statistics and stress. Until then physical `G3` is **UNRESOLVED** in the official framework and reveal is withheld. Tests still continue on their own diagnostic branches.
