# SST v0.8.19 Route A parallel derivation/falsification pack

Status: **[RESEARCH-TRACK] [PREREGISTERED] [FALSIFICATION-HARNESS]**

This pack tests whether Route A can be derived or falsified by three pre-registered model families:

1. **Onsager/KT-like vortex gas** — ordinary vortex-gas/core-cutoff density.
2. **Crofton/stereology** — isotropic line piercing geometry.
3. **Torsion-channel phase-space counting** — Weyl-style transverse/torsion channel counts.

The target is evaluated only for comparison:

```tex
\sigma_{\rm pierce}\Lambda_L = \frac{1}{2L_p^2}
```

Numerically:

```text
sigmaLambda_target = 1.914036558578934e+69 m^-2
target spacing     = 2.285729775093407e-35 m
t_p reference      = 5.391246446661944e-44 s
```

## Main verdict

**No non-fitted model in this pack derives the Route-A target.** Crofton/stereology derives the projection factor `1/2`, but not the line-density scale. Naive Onsager/KT/core packing misses the target by about 40 orders of magnitude. Strict Weyl/torsion phase-space counting misses by about 3--9 orders depending on whether a single or paired channel count is used. The old `16/pi^2` seed is retained only as a negative-control / archived trial relation.

## Files

- `scripts/routeA_parallel_derivation_falsification.py` — main reproducible harness.
- `results/routeA_parallel_derivation_falsification_results.json` — structured results.
- `results/routeA_parallel_derivation_falsification_models.csv` — compact model table.
- `results/routeA_parallel_derivation_falsification_report.md` — script-generated report.
- `docs/ROUTE_A_PARALLEL_DERIVATION_REPORT.md` — reviewer-facing analysis.
- `canon_blocks/SST_CANON-v0.8.19-routeA-preregistered-falsification-block.tex` — copy-ready research-track LaTeX block.
- `review_prompts/CLAUDE_GEMINI_ROUTE_A_REVIEW_PROMPT.md` — prompt for independent audit.

## Run

```bash
python scripts/routeA_parallel_derivation_falsification.py
```

This regenerates the JSON/CSV/report outputs in `results/`.
