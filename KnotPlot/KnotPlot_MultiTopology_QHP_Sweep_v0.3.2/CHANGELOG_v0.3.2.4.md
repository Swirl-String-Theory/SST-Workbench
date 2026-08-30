# v0.3.2.4

- Recover Stage-1 metrics from already-computed `.k float` states.
- Parse multi-component LOCF chunks directly.
- Define link length as sum of closed component lengths.
- Define link Rg as global bead-weighted radius of gyration.
- Preserve separate dL/L0 and dRg/Rg0 in recovered reports.
- Do not infer or fabricate the unavailable KnotPlot `/s` safeness metric.
- Detect `unknown data field`, `no data format set`, and `0 data records written`.
- Patch future KPC/source literal `/I,/l,/g,/N,/s` -> `/I,/l,/g,/N`.
- Back up original broken analysis before replacement.
