# Validation record — v0.1.0

Validation environment: Linux x86_64, Python 3.13, GCC 14.2, CMake 3.31.

Executed successfully:

```text
python -m compileall sst21d scripts tests
python -m pytest
5 passed
python -m sst21d build-native
python -m sst21d static --database examples/ideal_mini.txt --samples 256 ... --require-native
python -m sst21d convergence --database examples/ideal_mini.txt --resolutions 64 128 256 ...
python -m sst21d dynamic --trajectory examples/demo_trajectory.npz --time-unit s --length-unit m ...
python -m sst21d export ... --format both
python -m sst21d analyze-xyz ...
```

Selected smoke results:

```text
circle sampled length        = 6.2830276023
circle sampled reach proxy   = 0.999999999999
circle L/D proxy             = 3.1415138011
synthetic dispersion p       = 1.0388737513
synthetic minimum Q_geom     = 0.9968051145
synthetic minimum Q_phase    = 0.9909361835
```

The full user `ideal_favorites.txt` was identified and its schema was used, but it was not copied into this generated archive. The user should place that original file under `data/ideal_favorites.txt`; the pipeline records its SHA-256.

No claim is made here that the catalogue labels were independently recomputed, that sampled reach is exact thickness, or that static curves determine phase dynamics.
