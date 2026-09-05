# v0.2.3

- Continues all 20 frozen q/h/p states from 100k to 200k.
- Checkpoints: 120k, 140k, 160k, 180k, 200k.
- 100k metric-neutral reload gate before continuation.
- Same zero-track settlement thresholds as v0.2.2.
- Adds frozen-panel boundary/escape classification.
- Interpolates ΔL/L0 and ΔRg/Rg0 separately at the zero.
- Adds true-geometric-fixed-point vs compensating-balance classification.
- Uses robust Windows byte-stream source importer.
- Timing bookkeeping uses elapsed_seconds consistently.
