# SST Multi-Topology Panel Report

Overall panel classification: **4_PASS_29_FAIL**

> Overall is descriptive: individual topologies are classified independently; one unstable topology does not invalidate the panel.

## Unblinded summary

| source | class | components | status | growth | nearest rate | TBK penalty | ringdown | RPO |
|---|---|---:|---|---:|---:|---:|---|---|
| amfpower__4 | knot | 1 | FAIL | 0.1228 | 0.021963 | -0.0013 | PASS | NO |
| elecforce__off | knot | 1 | FAIL | 0.4712 | 0.023847 | -0.1434 | PASS | NO |
| thfstrength__0p02 | knot | 1 | PASS | 0.0054 | 0.042948 | -0.0060 | PASS | NO |
| mechforce__off | knot | 1 | FAIL | 0.9690 | 0.30814 | 0.0051 | FAIL | NO |
| tinc__60 | knot | 1 | FAIL | 0.1513 | -0.09711 | -0.0686 | PASS | NO |
| tanmag__0p025 | knot | 1 | FAIL | 0.2088 | 0.002564 | -0.1240 | PASS | NO |
| power__3 | knot | 1 | FAIL | 0.2119 | -0.00873 | -0.0401 | PASS | NO |
| hooke__4 | knot | 1 | FAIL | 0.5022 | 0.02695 | -0.1601 | PASS | NO |
| thfstrength__0p01 | knot | 1 | FAIL | 0.1377 | 0.043516 | -0.0889 | PASS | NO |
| tanforce__on | knot | 1 | FAIL | 0.3442 | 0.0033628 | -0.1033 | PASS | NO |
| mechforce__on | knot | 1 | FAIL | 0.1632 | 0.022364 | -0.0034 | PASS | NO |
| syrmag__4 | knot | 1 | FAIL | 0.1506 | -0.0028443 | 0.0423 | PASS | NO |
| charge__60 | knot | 1 | PASS | 0.0016 | 0.055561 | 0.0028 | PASS | NO |
| thfstrength__0p0025 | knot | 1 | FAIL | 0.1670 | 0.022346 | -0.0033 | PASS | NO |
| syfmag__1 | knot | 1 | FAIL | 0.1391 | -0.0017342 | 0.0290 | PASS | NO |
| hooke__0p25 | knot | 1 | FAIL | 0.0006 | 0.021503 | 0.0002 | FAIL | NO |
| sytmag__4 | knot | 1 | FAIL | 0.1329 | -0.036136 | -0.0127 | PASS | NO |
| thfstrength__0p04 | knot | 1 | FAIL | 0.0128 | 0.0039039 | -0.0035 | FAIL | NO |
| hooke__0p5 | knot | 1 | PASS | 0.0025 | 0.017603 | -0.0001 | PASS | NO |
| syfmag__4 | knot | 1 | FAIL | 0.1509 | -0.0034487 | 0.0275 | PASS | NO |
| syfmag__0p25 | knot | 1 | FAIL | 0.2092 | -0.0024118 | -0.0696 | PASS | NO |
| bencon__0p25 | knot | 1 | FAIL | 0.1633 | 0.022364 | -0.0034 | PASS | NO |
| bencon__4 | knot | 1 | FAIL | 0.1637 | 0.022363 | -0.0034 | PASS | NO |
| sytmag__0p25 | knot | 1 | FAIL | 0.1514 | -0.0016032 | 0.0216 | PASS | NO |
| bencon__1 | knot | 1 | FAIL | 0.1634 | 0.022364 | -0.0034 | PASS | NO |
| thermalforce__on | knot | 1 | PASS | 0.0822 | 0.02334 | -0.0630 | PASS | NO |
| amechforce__on | knot | 1 | FAIL | 0.0025 | 0.021151 | -0.0007 | FAIL | NO |
| amfpower__1 | knot | 1 | FAIL | 0.0011 | 0.021196 | 0.0002 | FAIL | NO |
| tinc__3p75 | knot | 1 | FAIL | 0.1247 | 0.01744 | 0.0011 | PASS | NO |
| charge__3p75 | knot | 1 | FAIL | 0.4072 | 0.012608 | -0.1201 | PASS | NO |
| power__7 | knot | 1 | FAIL | 0.4200 | 0.012488 | -0.1245 | PASS | NO |
| tanmag__0p4 | knot | 1 | FAIL | 0.4333 | 0.0091143 | -0.1266 | PASS | NO |
| syrmag__0p25 | knot | 1 | FAIL | 0.2207 | -0.0023844 | -0.0930 | PASS | NO |

## Interpretation

- `P2` tests reduced linear shape stability, not topological conservation.
- `P3` is a local sign test: positive separation does **not** imply global stability.
- `P4` asks whether coupling between the operational breathing/torsion/Kelvin families reduces the dominant growth rate.
- For links, `P6` checks pairwise Gauss-linking conservation during the short no-reconnection evolution.
- `P7` is deliberately strict: Floquet analysis is not claimed unless a genuine excursion-and-return is first found.
