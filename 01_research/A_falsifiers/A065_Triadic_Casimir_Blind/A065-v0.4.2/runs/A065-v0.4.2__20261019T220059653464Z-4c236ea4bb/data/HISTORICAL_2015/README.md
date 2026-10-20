# SST Historical Trefoil XYZ Seeds v0.1.0

Two **geometrical** trefoil centerlines, transcribed from 2015 notebook formulae:

- `A_Fourier_2015_p32_N1200_arclength.xyz` — p. 32, Fourier trefoil:
  `X(t) = (cos(t)+1.5*cos(2*t), sin(t)-1.5*sin(2*t), 0.35*sin(3*t))`
- `B_Torus_2015_p66_N1200_arclength.xyz` — p. 66, toroidal trefoil:
  `X(t) = ((2+cos(3*t))*cos(2*t), (2+cos(3*t))*sin(2*t), sin(3*t))`

There are also `N600` versions for grid-refinement comparisons. **All coordinates are
in the dimensionless, unscaled historical geometry units.** The orientations and
relative size/shape differences are preserved; no normalization to common length
is performed.

## File format

- ASCII UTF-8, **headerless** `.xyz`, **exactly three whitespace-separated values** (`x y z`) per line;
- `600` or `1200` vertices per file, no duplicated endpoint (`t = 2*pi` omitted);
- periodic closed curve assumed; analyses must connect final vertex back to first;
- points resampled to near-equal *arclength* spacing, not equal `t` steps;
- scientific notation with 16 digits after decimal;
- no `.xyz` chemical-atom count line. This is point-cloud/centerline XYZ, not the molecular XYZ convention.

## Numerical details

Length obtained by integrating the Euclidean speed `||dX/dt||` on `[0,2*pi]`.
Parameter points are inverted from the cumulative arc-length integral using a
monotone PCHIP interpolation of 262144 subintervals. The plotted polygon
length is slightly shorter than the analytic-curve length (chord approximation).

| Seed | Analytic curve length, nondimensional |
|---|---:|
| Fourier A | 19.976521990340952 |
| Toroidal B | 31.898600666412335 |

## Reproducibility

```sh
python -m pip install numpy scipy
python regenerate.py
```

SHA256 digests, numerical diagnostics and formulas are in `manifest.json`.
`regenerate.py` contains internal checks of periodicity, convergence of
arclength integration, finite coordinates, strictly monotone sampling and near-equal edge lengths.

## Scientific limitations

These are **initial geometric seed curves only**, not results of any PKLSA or
finite-core Biot-Savart/Euler evolution. They do not define core radius,
fluid density, circulation, physical mass, units, or a 3D velocity field.
Do not promote to physical conclusions before applying the independent
qualification gates (finite core, nonintersection and topology, resolution,
conservation, numerical convergence, and evolution).

Use the 600/1200 pair to test discretization sensitivity. Keep each seed's
original unscaled geometry as an immutable reference; matching physical
arclength across seeds requires a separately documented transformation.
