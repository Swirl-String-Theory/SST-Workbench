# Preregistration — Trefoil Balance Point Campaign v0.2.1

This campaign refines the long-time K31 expansion/contraction zero found by v0.2.0.

Only `load 3.1` is run. T(2,3) remains a later independent control.

The 20 frozen q/h/p points are on:
- `q = 15 + 22.27046411874018*t`
- `h = 1 + 0.3563655804274017*t`
- `p = 5 + t`

with frozen `t`:
`1.215, 1.220, 1.225, 1.230, 1.235, 1.240, 1.245, 1.250, 1.255, 1.260,
1.265, 1.270, 1.275, 1.280, 1.285, 1.290, 1.295, 1.300, 1.310, 1.320`.

`t=1.250` repeats v0.2.0 R05 solely as a reproducibility diagnostic.

## Long horizons

Standard: every setting to **30,000** iterations, with checkpoints:
`0,10,25,50,100,250,500,1000,2000,4000,6000,8000,10000,12500,15000,20000,25000,30000`.

Extended: every setting continues from its saved i30000 state to **60,000**, with additional:
`40000,50000,60000`.

The extension is never candidate-only; all 20 states are continued.

## Late equilibrium gate

For the active late window, a direct measured equilibrium requires:
- `abs(median(E_late)) <= 3.0e-4`
- `abs(late drift per 1000) <= 7.5e-5`
- `late span <= 6.0e-4`

The analyzer also tracks the interpolated zero versus time. A zero that keeps migrating is not accepted as settled.

This remains a geometric expansion/contraction balance surrogate, not a direct force measurement.
