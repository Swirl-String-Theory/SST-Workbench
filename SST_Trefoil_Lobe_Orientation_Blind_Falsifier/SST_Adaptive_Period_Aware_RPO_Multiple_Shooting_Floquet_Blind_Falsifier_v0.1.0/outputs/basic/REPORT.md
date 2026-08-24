# Adaptive Period-Aware RPO + Multiple-Shooting + Floquet Report

Campaign: **RPO_BASIC_period_aware_deterministic**

> RPO/Floquet is an additional dynamical-coherence gate. It does not replace the N=720 adaptive spectral stability ladder.

| source | family | screen growth | spectral | direct RPO | shooting RPO | Floquet | class |
|---|---|---:|---|---:|---:|---:|---|
| charge__60 | charge | 0.00164261 | PENDING | NO | NO | N/A | **NO_CERTIFIED_RPO** |
| hooke__0p5 | hooke | 0.00249077 | PENDING | NO | NO | N/A | **NO_CERTIFIED_RPO** |

## Fixed certification gates

- excursion >= 0.0075
- recurrence <= 0.025
- return/peak <= 0.5
- Floquet rho(non-neutral) <= 1.03

## Interpretation

- `NO_CERTIFIED_RPO` does **not** prove that no RPO exists; it means none was certified inside the preregistered eigenmode/amplitude/phase/horizon domain.
- `SPECTRAL_PENDING` means an RPO result may be interesting dynamical evidence but is not yet a complete SST stability certification.
- The period horizon was measured from `Im(lambda)` and never introduced as a free restoring frequency.
