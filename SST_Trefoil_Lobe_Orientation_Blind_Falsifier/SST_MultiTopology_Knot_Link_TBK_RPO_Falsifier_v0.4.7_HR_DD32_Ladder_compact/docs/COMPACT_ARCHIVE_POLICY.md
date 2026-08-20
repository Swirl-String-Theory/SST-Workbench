# Compact Archive Policy — v0.4.5.3+

The previous recursive ZIP-in-ZIP policy caused exponential release growth. v0.4.5.2 reached roughly 257 MB compressed while the executable source tree and preserved datasets require only a small fraction of that size.

## Keep as full embedded artifacts

- one exact **scientific capsule**: v0.4.1;
- full Fremlin source archive;
- full KnotPlot/RidgeRunner source archive;
- current source/configs/scripts;
- summary-level historical reference results.

v0.4.1 is sufficient as the historical capsule because it already embeds the exact v0.1.0, v0.1.1, v0.2.0, v0.3.0 and v0.4.0 releases.

## Keep as metadata only

Runtime-only maintenance releases v0.4.2 through v0.4.5.2 are not recursively embedded. Their original SHA-256 values are retained in `release_history/HISTORICAL_HASHES.sha256`, and their changes remain in `CHANGELOG.md`.

## Do not package

- nested copies of runtime-only ZIPs;
- generated virtual environments;
- build products;
- Python caches;
- large per-blind-object historical reference JSON/NPZ snapshots when a summary/verdict and recomputation path already exist.

A future release should only add another full historical ZIP when it changes the scientific model, preregistered gate semantics, datasets, perturbation basis, or other information required to reconstruct a scientifically distinct result.
