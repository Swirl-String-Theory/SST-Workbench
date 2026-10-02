# Provenance-clean fluid circulation input

Primary fluid input is a raw closed-loop velocity-field sample:

`circulation_loop.csv`

Schema:

```csv
x_m,y_m,z_m,vx_m_s,vy_m_s,vz_m_s
...
```

The pipeline computes

\[
\Gamma=\oint \mathbf v\cdot d\boldsymbol\ell
\]

with a closed-loop trapezoidal line integral.

A matching `circulation_provenance.json` is mandatory. The primary action gate is INVALID
unless every dependency flag is explicitly false and status is `INDEPENDENT_MEASURED`.

This is intentional: the canonical SST \(\Gamma_0=2\pi r_c v\) is not used in the primary
gate because the current \(r_c\) chain is Compton/\(\hbar\)-calibrated.
