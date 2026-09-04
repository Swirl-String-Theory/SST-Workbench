# Optional SSTcore Bridge

`src/sstcore_bridge.py` can use an installed SSTcore wheel exposing `VortexKnotSystem`.

Example:

```bash
python src/sstcore_bridge.py \
  --knot trefoil \
  --resolution 128 \
  --dt 0.0001 \
  --steps 20 \
  --output outputs/sstcore_trefoil.json
```

The bridge is intentionally labelled a **cross-backend diagnostic**. SSTcore's native evolution may use a different core kernel, timestepper or remeshing convention from `sst_dimensionless_ratios.py`. Its result must not be inserted into the same ratio table until the native operator has been audited and matched.

The bridge currently:

- initializes a native trefoil, figure-eight or named bundled knot;
- evolves it with SSTcore;
- normalizes and resamples the before/after centerlines;
- computes standalone static diagnostics on both;
- computes recurrence modulo rigid rotation and cyclic shift;
- records the installed SSTcore version.
