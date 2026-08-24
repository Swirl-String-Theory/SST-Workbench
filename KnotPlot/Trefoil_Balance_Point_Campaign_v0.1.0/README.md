# Trefoil Balance Point Campaign v0.1.0

Focused prospective balance search:

\[
10\ q/h/p\ settings \times 2\ trefoil\ embeddings = 20\ runs.
\]

Embeddings:

```text
K31 -> load 3.1
T23 -> torus 2 3 300
```

Both are normalized to 300 beads and `fitto mindist 1.05`.

The settings are:

| ID | q | h | p | role |
|---|---:|---:|---:|---|
| B00 | 15 | 1 | 5 | baseline |
| R25 | 20.567616 | 1.089091 | 5.25 | full ray |
| R50 | 26.135232 | 1.178183 | 5.5 | full candidate |
| R75 | 31.702848 | 1.267274 | 5.75 | full ray |
| R100 | 37.270464 | 1.356366 | 6 | full ray |
| QLO | 21.5 | 1 | 5.5 | q bracket low |
| QCEN | 23.54 | 1 | 5.5 | reduced candidate |
| QHI | 25.5 | 1 | 5.5 | q bracket high |
| HLO | 26.135232 | 1.05 | 5.5 | hooke bracket low |
| HHI | 26.135232 | 1.30 | 5.5 | hooke bracket high |

Every run writes:

```text
i00000 i00025 i00100 i00500 i01000 i04000 i10000
```

so the analyzer can measure the **early signed expansion/contraction response**,
not only the 10k endpoint.

Recommended target-machine sequence:

```bat
run_00_install.cmd
run_02_verify_preregistration.cmd
run_05_generate.cmd
run_10_validate_syntax.cmd
run_20_smoke_two_variants.cmd
```

If both baseline embeddings pass:

```bat
run_30_campaign.cmd
run_40_analyze.cmd
run_90_pack_outputs.cmd
```

or simply:

```bat
run_all.cmd
```

The campaign can identify a common geometric zero across two trefoil embeddings.
A later perturbation campaign is still required to establish restoring
stability around that zero.
