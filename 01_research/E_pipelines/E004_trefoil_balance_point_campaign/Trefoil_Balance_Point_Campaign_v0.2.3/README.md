# Trefoil_Balance_Point_Campaign_v0.2.3

Continuation of the metric-neutral K31 balance campaign from 100k to 200k.

Run:

```bat
run_all.cmd
```

Place the folder next to either:

```text
Trefoil_Balance_Point_Campaign_v0.2.2_outputs.zip
```

or the completed v0.2.2 working folder.

## Why 200k rather than 400k?

At 100k:

```text
t* = 1.292108327
panel max = 1.320
```

Observed 10k zero increments have only fallen from `0.003880` to
`0.002851`.

Two planning extrapolations give:

```text
              200k       400k
geometric     1.313835   1.334608
power-law     1.317070   1.356833
```

The existing frozen panel stops at `t=1.320`. Therefore 200k is the correct next
decision horizon; a 400k run would likely require a preregistered panel extension.

## New outcomes

- `MOVING_LATE_BALANCE_ZERO`
- `ZERO_AT_FROZEN_RANGE_BOUNDARY`
- `ZERO_LEFT_FROZEN_PANEL`
- `SETTLED_COMPENSATING_BALANCE_ZERO`
- `TRUE_GEOMETRIC_FIXED_POINT_CANDIDATE`

The last classification requires not only a settled zero-track but also stationary
separate ΔL/L0 and ΔRg/Rg0 trends at the interpolated zero.
