# Trefoil Balance Point Campaign v0.2.2 — preregistration

## Scientific question

Does the metric-neutral K31 q/h/p balance zero that migrated from

`1.268994713` at 30k to
`1.279933293` at 60k

settle by 100k, or does it continue to migrate?

## Frozen parameter panel

All 20 q/h/p states Q01..Q20 are copied **exactly** from v0.2.1.
No parameter insertion, deletion, narrowing, or candidate-only continuation is allowed.

## Continuation

- input state: each frozen setting's metric-neutral `i60000.k`
- checkpoints: `70000,80000,90000,100000`
- all 20 states are continued
- no `fitto`, `refine`, or `centre` is permitted between checkpoint load and the first resumed `ago`
- a separate 60k reload probe must pass before continuation

## Primary asymptotic gate

For interpolated zero positions t*(i) at 70k, 80k, 90k, 100k:

- a crossing must exist at every late checkpoint;
- absolute OLS zero-track slope <= `0.0010 t per 10000 iterations`;
- last-three zero-position spread <= `0.0025`.

The outcome is `SETTLED_LATE_EQUILIBRIUM_FOUND` only if these zero-track
conditions pass **and** at least one fixed QHP state passes the inherited late-E gates.

Otherwise, if the crossing remains measurable but the zero-track gate fails,
the result is `MOVING_LATE_BALANCE_ZERO`.

## Inherited fixed-state gates

- |median(E_late)| <= 3e-4
- |dE/di| <= 7.5e-5 per 1000
- late E span <= 6e-4

Late window: 70k,80k,90k,100k.

## Diagnostic strengthening

`ΔL/L0` and `ΔRg/Rg0` are reported separately. They are not new acceptance
gates in v0.2.2, but they expose cancellation inside the averaged E observable.

## Source provenance

The repaired v0.2.1 output used to define this continuation had SHA-256:

`f63cd48a3d85a5c17b2e5d90f6185bfad0969e49c4f4ca8113a32cef882bac19`

Its 30k→60k reload continuity audit was `PASS`.
