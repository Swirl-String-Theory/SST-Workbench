# SST Historical Trefoil XYZ — v0.2.1

Two historical parametric trefoil seeds from 2015, page 32 (Fourier) and page 66 (torus), in four geometric variants each:

- `orig_ccw`: original geometry, natural increasing-parameter traversal;
- `orig_cw`: original geometry, reverse traversal;
- `mirrorX_ccw`: reflected chirality (`x -> -x`), natural traversal;
- `mirrorX_cw`: reflected chirality, reverse traversal.

CW and CCW are file-order labels, **not** absolute 3D rotation directions. The first vertex is preserved when reversing traversal. A reflected knot is a true mirror; an orientation reversal is not a mirror.

Default output: 600 and 1200 vertices each, so 16 `.xyz` files. N below 600 is rejected. Headerless ASCII, exactly three space-delimited `x y z` coordinates per line; implicit periodic closure and no duplicated terminal vertex. All coordinates dimensionless. These are historic geometries, **not** dynamical vortex states, physical circulation prescriptions, or independently computed Swirl Clock frequencies.

Install requirements:

```bash
python -m pip install numpy scipy
```

Generate default resolution:

```bash
python regenerate.py
```

Choose your own resolutions, every one >= 600:

```bash
python regenerate.py --n 600 1200 2400
```

Specify directory:

```bash
python regenerate.py --n 1200 --out ./xyz
```

Inspect `manifest.json` for SHA-256 checksums and geometric diagnostics.
