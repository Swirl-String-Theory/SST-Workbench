# v0.3.1 syntax-verified rebuild

- Rebuilt from the earlier v0.3.1 parameter manifest and `parameters_full_source.txt`.
- Removed stale copied matrix outputs/logs/caches from the release.
- Parameter values are always emitted as `name = value`.
- `tinc` is the runtime parameter; `timeincr` is not emitted.
- Added explicit `collision fast` and `energy model MD` common action baseline.
- Added static validation that every used parameter exists in the runtime dump.
- Added static action-vs-assignment KPC audit.
- Runner creates save/coords parent directories before KnotPlot starts.
- Added local `.venv` install stage.
