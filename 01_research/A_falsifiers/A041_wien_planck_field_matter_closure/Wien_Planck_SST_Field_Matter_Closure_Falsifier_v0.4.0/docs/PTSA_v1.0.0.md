# SST Parametric Trefoil Seed Atlas v1.0.0

**Canonical short name:** PTSA v1.0.0.

This replaces the informal phrase `shader-derived set` in scientific output. `Shader-inspired` remains only a provenance note. The dataset is an independent analytic implementation, not redistributed renderer code.

## Fixed grid

- `baseR`: 3.5, 4.08248290463863, 4.6
- `bulge_R = a`: 1.4, 1.8, 2.2, 2.6
- `z_weave = b`: 2.2, 3.0, 3.8, 4.6
- `plane_offset`: -2.886751345948129
- `p=2`, `q=3`
- 512 raw points per candidate
- 48 candidates total

The action solver normalizes every candidate to total arclength `L_hat=1`, so the grid explores shape rather than an absolute SI scale.
