# Development basis: A056-v0.3.0 real-filament G2 result

This file records the motivation for the new v0.4.0 test and explicitly marks it **development-only**.

The read-only v0.3.0 diagnostic reported four admissible real-filament cases. Their top-three raw-POD energy fractions were between `0.9999613238419243` and `0.9999952827122585`, and their POD orthogonality residuals were at machine precision (`4.18e-16` to `1.66e-15`). Nevertheless, their early/late raw-POD subspace overlaps were:

```text
0.7087974858720588
0.6279136205256063
0.7326808739451738
0.7123071222867935
```

All therefore failed the v0.3.0 blocking threshold `>= 0.85` while remaining strongly low-dimensional. v0.4.0 does not reinterpret that historical run as a pass and does not lower 0.85. It asks a new preregistered question using circular/Fourier metrics on fresh `m=4`, `epsilon=0.03` provider data.

The exact diagnostic snapshot is retained at `data/development/A056_v0.3.0_G2_DIAGNOSTICS_READONLY.json` and is not consumed by the v0.4.0 pipeline.
