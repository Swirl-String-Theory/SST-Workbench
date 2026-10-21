# SST Mathematical Evidence Registry v0.1.0

**DEVELOPMENT — NOT SCIENTIFICALLY CERTIFIED — 20 October 2026**

## Purpose
A versioned, source-traceable research **index and evidence register**, not a physics-certification report. Separates syntactic extraction, paper-summary claims, conditional mathematical derivations, numerical consistency checks, physical validation and falsification.

## Scope
- `sources/`: immutable *copies* of 11 uploaded files (one SST summaries Markdown, one VAM summaries PDF, nine primary papers). Fingerprints in `results/source_manifest.json`.
- `results/raw_formula_candidates.jsonl`: every `$$...$$` from the SST Markdown. **NONE** are promoted to proof: `NOT_REVIEWED`. Exact line ranges and raw content retained. **No latex auto-cleaning**.
- `results/paper_inventory.csv`: all SST-00…90 and VAM-01…15 IDs, with assessment-heading coverage flags.
- `results/curated_claims.jsonl`, `curated_claims.csv`: 41 manually inspected specific claims and mathematics, in the original paper where available. Includes explicit scopes, units, epistemic status, falsifier, citations to source/page. These are selected claims only, NOT an exhaustive audit of the corpus.
- `results/issues.csv`: high-impact errors and no-go results, cross-referenced to claim IDs.
- `results/qualification_summary.json`: counts, numerical examples, provenance limitations.
- `registry_report.pdf` and `registry_report.tex`: human-readable scientific report.

## Verify
On Windows run `run_all.cmd`, or on Linux/macOS run `bash run_all.sh`. The script rebuilds data deterministically and executes `unittest` checks. Only the optional PDF page-count and Voigt tests need `PyMuPDF`, `numpy`, `scipy`; those skip if dependencies are missing. `build_registry.py` itself uses only Python standard library.

## Epistemic scheme
- `ESTABLISHED_WITH_ASSUMPTIONS`: standard mathematical theorem/result **under explicitly listed assumptions**, not an SST physical verification.
- `CONDITIONAL_*`: mathematics valid conditional on model/inputs.
- `MATHEMATICAL_CONSTRUCTION` and `MATHEMATICAL_ANSATZ`: well-defined model/functional, physical provenance unproved.
- `HYPOTHESIS_UNTESTED`, `UNRESOLVED`, `POSTULATED_CLOSURE`: cannot promote to physical claim.
- `INCONSISTENT`, `NUMERICALLY_INCONSISTENT`, `DIMENSIONALLY_INCONSISTENT`: corrections/no-go items.
- Every raw summary-extracted formula is `NOT_REVIEWED`, even when old source labels say `[DERIVED]` or `[ORTHODOX]`.

## IMPORTANT LIMITS
1. Older AI ratings in the SST and VAM summary bundles are index terms, not scientific evidence or referee reports.
2. Only a subset of original papers was available. SST-65 and SST-82 are not explicitly mentioned in the SST Markdown; presence or absence of actual manuscripts is not claimed.
3. No native PKLSA package or certified Euler solver has been connected to this registry, and no physical Maxwell/gravity/particle claim is certified.
4. Some source-derived equations reproduce externally supplied constants or known theory **by construction**. This is not an independent prediction.
5. We have not edited/replaced any original source manuscripts. The registry records contradictions and repairs separately.

## Proposed subsequent gates
`G0` provider provenance, `G1` manuscript/summary concordance, `G2` dimensions and symbol contracts, `G3` symbolic derivation, `G4` independently reproducible numerical result, `G5` convergence, `G6` branch-blind falsifier, `G7` physical interpretation/experimental claim.

## Installation in SST-Workbench
Recommended destination (new, not overwriting existing frameworks): `02_libraries/C_mathematical_evidence/SST_Mathematical_Evidence_Registry/SST_Mathematical_Evidence_Registry_v0.1.0/`. This is a proposed location; no Google Drive upload has been performed.

## Search
`python query_registry.py Kelvin` searches curated claims. Examples:

- `python query_registry.py --paper SST-29`
- `python query_registry.py --status DIMENSIONALLY_INCONSISTENT`
- `python query_registry.py --source raw --paper SST-00`
- `python query_registry.py --source both --json 'helicity|Gamma'`

Raw candidates remain unreviewed regardless of the query.
