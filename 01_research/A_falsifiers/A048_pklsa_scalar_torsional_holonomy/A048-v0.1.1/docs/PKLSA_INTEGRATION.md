# PKLSA integration contract — A048 v0.1.0

A048 targets the trefoil population first.

Expected root content:

```text
manifests/CANDIDATES_FULL.jsonl   (or .csv)
families/14_knot_3p1.npz
```

The signed trefoil contract used here is:

- family: `knot_3.1`;
- canonical ID: `3_1`;
- family index: 14;
- variants: 48;
- components: 1;
- points/component: 512;
- array shape: `(48,1,512,3)`;
- expected SHA-256: `ffc31331fccaf10a3171e4ccbf3ec0043e56ff681f85cc8b8149932193d736d1`.

Each centerline is periodically resampled by closed arclength, centered, and uniformly scaled to unit RMS radius. No reflection or rotation is applied.

`pklsa_preview.py` currently computes geometry and exploratory operator spectra only. Those spectra are model predictions, not observed dynamics.
