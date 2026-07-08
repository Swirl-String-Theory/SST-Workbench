# SST v0.8.19 Planck Routes A--D: Equivalence-Corrected Evidence Pack

Status: **[RESEARCH-TRACK] [TRIAL] [NOT DERIVED] [FITTED]**.

This v2 pack supersedes the previous A--D evidence pack. The earlier framing as four converging route candidates is rejected. The corrected interpretation is stricter:

> Routes A--D are four algebraic representations of one seed relation, not four independent derivations.

The useful result is a precise research target for the missing SST vacuum-tangle / pressure-susceptibility lemma, not proof of Planck time.

## Central seed

```tex
G_* = (\pi^3/16) \rho_f \vchar^9 r_c^4/(M_e^2 c^7)
```

Numerically:

- `G_*/G_N = 0.994284248001`
- `t_p(G_*)/t_p = 0.997138079558`

Equivalent hbar/alpha form:

```tex
G_* = (\pi^3/2^17) \alpha_SST^13 \rho_f \hbar^4/(M_e^6 c^2)
```


### Constant-synchronization note

The route-C script value is `G_C = 6.636152035232503e-11`. The fully reduced horn-density seed value is `G_* = 6.636151356430562e-11`. Their ratio is `0.999999897712`. This tiny mismatch is not physics; it comes from the already-noted constant synchronization issue: the explicit `rho_core` used in scripts differs from `M_e c^2/(2 pi vchar^2 r_c^3)` by `1.023e-07`, and the Compton-core hbar closure differs from CODATA hbar by `7.170e-09`.

## What changed from v1

Removed / corrected:

- The claim that A--D are four independent converging routes.
- The claim that the shared residual is evidence for one missing kernel.
- Any canon-ready language suggesting Planck time has been derived.

Added:

- Equivalence lemma: B = 2 r_c^2 A, D = c^4/(4G_C), and A <-> C via the Compton-core closure.
- Look-elsewhere disclosure: 121,975 scan points; 31 within 5%; 5 within 0.575%; one better hit without density ratio.
- Degeneracy disclosure: exact closure requires rho_f = 7.040240e-07 kg/m^3; d ln G/d ln alpha = 13.
- Corrected v0.8.19 research-track block and patch.

## Recommended use

Send `docs/EXECUTIVE_SUMMARY_CORRECTED_FOR_REVIEWERS.md` plus `canon_blocks/SST_CANON-v0.8.19-research-track-planck-routes-A-D-equivalence-corrected-block.tex` to Gemini/Claude.

Do **not** apply the old Planck-route patch from v1. Apply only:

```bash
patch -p0 < canon_patches/SST_CANON-v0.8.19-research-track-planck-routes-A-D-equivalence-corrected.diff
```

The diff assumes LF line endings. If the project file is CRLF, normalize first.

## Files

- `audit/route_ABCD_equivalence_audit_report.md` -- human-readable corrected audit.
- `audit/route_ABCD_equivalence_audit.json` -- numerical audit payload.
- `audit/route_ABCD_look_elsewhere_top25.csv` -- top scan hits.
- `scripts/route_ABCD_equivalence_scan_audit.py` -- reproducible audit script.
- `canon_blocks/` -- corrected LaTeX blocks.
- `canon_patches/` -- corrected v0.8.19 research-track patch plus independent Route-I heat-guard patches.
- `evidence/` -- original route A--D trial evidence retained for reproducibility, with corrected interpretation.

## Bottom line

The pack is still useful, but its epistemic status is lower and cleaner:

```tex
[RESEARCH-TRACK] [TRIAL] [NOT DERIVED] [FITTED]
```

The real canonization target is now:

```tex
sigma_pierce Lambda_L = 1/(2 L_p^2)
```

derived independently from SST vacuum-tangle statistics, preferably through an Onsager/KT-style vortex-density theorem.
