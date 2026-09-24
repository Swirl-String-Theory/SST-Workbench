# Validation — SST Euler Regularity / BKM Singularity Gate v0.2.0

## Software status

**PASS — 6/6 packaged tests.**

Validated:

1. legacy analytic trefoil native seed shape/finite values;
2. spectral solenoidal projection to roundoff;
3. ABC/Beltrami steady-flow RHS regression;
4. PKLSA 48-row trefoil census + `(48,1,512,3)` bundle schema using a generated schema fixture;
5. closed-arclength canonicalization + generic native centerline vorticity kernel;
6. convergence isolation: three distinct geometries cannot be pooled, while three spatial replays of one geometry can satisfy the synthetic escalation logic.

## End-to-end PKLSA-schema smoke

A **software-only schema fixture** was generated from the frozen real PKLSA trefoil census metadata and the published PTSA parameter grid. It is explicitly not the signed PKLSA payload and therefore is not scientific evidence.

Smoke selection: variants 0, 23, 47; `N=16`, `dt=0.003`, `T=0.036`.

| case | energy relative drift | max divergence RMS | max-vorticity growth | BKM fit candidate |
|---|---:|---:|---:|---|
| anonymous 1 | 2.7591e-12 | 1.1579e-16 | 1.01211 | false |
| anonymous 2 | 1.5464e-11 | 1.3341e-16 | 1.02484 | false |
| anonymous 3 | 2.1674e-11 | 1.2156e-16 | 1.02527 | false |

Smoke verdict: `NO_CONVERGED_BKM_CANDIDATE_IN_WINDOW`.

This smoke verdict has **no physical evidential status** because the signed `families/14_knot_3p1.npz` payload was not used.

## Signed PKLSA scientific run status

**NOT RUN in this environment.**

The accessible PKLSA v0.1.1 Google Drive folder contains README/provenance/manifests and the adapter code, and its package manifest declares the family payloads. However, the directly listable Drive folder available to this session does not expose the `families/14_knot_3p1.npz` binary. The v0.2.0 scientific configs therefore fail closed rather than silently substituting reconstructed coordinates.

Expected signed trefoil bundle SHA-256:

`ffc31331fccaf10a3171e4ccbf3ec0043e56ff681f85cc8b8149932193d736d1`

When the complete local PKLSA root is supplied to `run_all.cmd`, the hash and shape are checked before Euler evolution begins.
