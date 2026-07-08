# SST v0.8.19 Planck Routes v3 — Preregistered All-Inclusive Evidence Pack

Status: **[RESEARCH-TRACK] [TRIAL] [NOT DERIVED] [FITTED]**.

This v3 pack supersedes the earlier Planck Routes A--D evidence packs.  Older files are retained under `archive/`, but the current interpretation is stricter:

> Routes A--D are not four independent derivations. They are four algebraic representations of one trial seed relation, plus a look-elsewhere-controlled target generator for Route A.

## Current scientific verdict

The earlier “common residual” framing is rejected.  The common residual appears because the four routes reduce to one algebraic seed relation once the Compton--core and horn-density closures are used.

The single seed relation is

```tex
G_\star = \frac{\pi^3}{16}\,\frac{\rho_{\!f}\,\vchar^9 r_c^4}{M_e^2 c^7}
```

with the equivalent alpha/hbar form

```tex
G_\star = \frac{\pi^3}{2^{17}}\,\alpha_{\rm SST}^{13}\,\frac{\rho_{\!f}\hbar^4}{M_e^6c^2},\qquad \alpha_{\rm SST}=2\vchar/c.
```

The numerical proximity to `G_N` is not evidence after look-elsewhere correction.  It remains useful as a target and audit artifact.

## What is new in v3

1. Adds preregistration discipline: no new scans count as evidence.
2. Adds a Route-A target harness for `sigma_pierce * Lambda_L`.
3. Keeps old scripts and outputs under `archive/`.
4. Includes the user-shared exports/results in `archive/user_exports/`.
5. Regenerates audit JSON, report, and top-25 scan from the v3 script.
6. Provides corrected canon blocks and v0.8.19 research-track patch.

## How to run

From this folder:

```bash
python scripts/route_ABCD_equivalence_scan_audit_v3.py
python routeA_preregistered/routeA_vacuum_tangle_preregistered_target.py
```

Outputs appear in `results/` and `routeA_preregistered/results/`.

## Canon usage

Do **not** apply older Planck-route patches.  Use only:

```text
canon_patches/SST_CANON-v0.8.19-research-track-planck-routes-v3-preregistered.diff
```

The Route-I heat guard patch remains independently useful and is archived under `verification/`.

Patch note: the diff assumes LF line endings.  If your local canon file uses CRLF, normalize line endings before applying.

## What remains open

The real research task is Route A:

```tex
\sigma_{\rm pierce}\Lambda_L \stackrel{?}{=} \frac{1}{2L_p^2}
```

but `Lambda_L` and `sigma_pierce` must be derived independently from SST vacuum-tangle statistics.  `G`, `L_p`, `t_p`, and `F_gr^max` are forbidden as inputs to that derivation.
