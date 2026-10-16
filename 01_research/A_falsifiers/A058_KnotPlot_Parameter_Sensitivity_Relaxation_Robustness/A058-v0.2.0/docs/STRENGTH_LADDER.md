\
# A058-v0.2.0 strength ladder

Positive levels use exactly `m(k)=2^(k/4)` for `k=-16..16`, so `x=log2(m)=k/4` is uniformly spaced by 0.25 and reciprocal pairs satisfy `m(-k)=1/m(k)`. An exact `m=0` endpoint is added separately and never included in log/polynomial fits.

All non-strength relaxation controls are left at KnotPlot `reset all` defaults. The trefoil is loaded from `3.1` and resampled to 300 beads as the fixed discretization control.

Two strength axes are active under reset-all defaults and therefore share the global default `m=1` condition. The third strength term is reset-all-disabled, so its 34-level sweep explicitly enables that force; its own `m=1` condition is the axis reference and its `m=0` condition is a metamorphic equivalence test against the global reset-all baseline. Total: `1 + 33 + 33 + 34 = 101` scientific conditions.
