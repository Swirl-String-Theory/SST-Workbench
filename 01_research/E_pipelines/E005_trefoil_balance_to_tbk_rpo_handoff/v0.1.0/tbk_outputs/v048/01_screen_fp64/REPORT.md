# SST Multi-Topology Panel Report

Overall panel classification: **0_PASS_8_FAIL**

> Overall is descriptive: individual topologies are classified independently; one unstable topology does not invalidate the panel.

## Unblinded summary

| source | class | components | status | growth | nearest rate | TBK penalty | ringdown | RPO |
|---|---|---:|---|---:|---:|---:|---|---|
| BALX_005 | knot | 1 | FAIL | 0.6027 | 0.00014775 | -0.2987 | PASS | NO |
| BALX_004 | knot | 1 | FAIL | 0.2929 | -0.010658 | -0.0983 | PASS | NO |
| BALX_002 | knot | 1 | FAIL | 0.1593 | -0.034495 | 0.0367 | PASS | NO |
| BALX_006 | knot | 1 | FAIL | 0.5912 | 0.00015219 | -0.1760 | PASS | NO |
| BALX_001 | knot | 1 | FAIL | 0.2111 | -0.00049666 | 0.0288 | PASS | NO |
| BALX_008 | knot | 1 | FAIL | 0.5276 | 0.00015856 | -0.1238 | PASS | NO |
| BALX_003 | knot | 1 | FAIL | 0.5556 | 0.00015462 | -0.1446 | PASS | NO |
| BALX_007 | knot | 1 | FAIL | 0.2719 | -0.010265 | -0.1010 | PASS | NO |

## Interpretation

- `P2` tests reduced linear shape stability, not topological conservation.
- `P3` is a local sign test: positive separation does **not** imply global stability.
- `P4` asks whether coupling between the operational breathing/torsion/Kelvin families reduces the dominant growth rate.
- For links, `P6` checks pairwise Gauss-linking conservation during the short no-reconnection evolution.
- `P7` is deliberately strict: Floquet analysis is not claimed unless a genuine excursion-and-return is first found.
