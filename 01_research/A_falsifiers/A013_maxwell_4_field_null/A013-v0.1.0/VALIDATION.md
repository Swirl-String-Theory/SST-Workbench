# Validation snapshot

Date: 2026-08-13

The pure-Python synthetic validation suite was executed in the artifact environment.

```text
pytest: 1 passed
T01: PASS
T02: PASS
T03: PASS
T04: PASS
T05: PASS
T06: PASS
T07: REJECTED_NEGATIVE_CONTROL (expected)
```

Selected numerical results:

- T01 Stokes relative mismatch: `1.1045713621e-06`.
- T02 holonomy relative mismatch: `4.4283003020e-03`; Gauss linking `1.0000186699`.
- T03 moving-loop relative mismatch: `1.3051220666e-12`.
- T04 exterior curl residual: `4.7699048229e-05`; divergence residual: `4.6811537635e-09`.
- T05 ABC Beltrami residual: `1.8344290756e-11`.
- T06 conservative cycle work: numerical zero; antisymmetric negative control produces nonzero cycle work.
- T07 compact-vortex pressure candidate: fitted radial-RMS exponent `n = 6.9665381112`, not `2`; shell-flux CV `1.2779684137`. The Newtonian-like gate is therefore rejected as intended.

The validation proves software discrimination on analytic/synthetic controls only. It does not constitute an SST empirical validation.
