# CHANGELOG v0.1.0

- New single-package RPO falsifier; no fragmented subprojects.
- Uses measured `Im(lambda)` only to determine observation horizon.
- Scans multiple positive-imaginary eigenpairs instead of only the first oscillatory pair.
- Adds fixed amplitude and phase ladders.
- Adds physical-time chunk extension so adaptive CFL timesteps cannot silently shorten the intended horizon.
- Preserves strict R5 excursion / recurrence / return-ratio thresholds.
- Adds reduced multiple-shooting continuity refinement with fixed period-scale grid.
- Calls the exact v0.4.8 `floquet_multi` implementation only after certified RPO closure.
- Keeps deterministic and thermal/stochastic preparation branches separate.
- Consumes existing screen Jacobians (`*_arrays.npz`) to preserve exact prior linearization provenance.
- If spectral-extension results exist, can require spectrally converged P2 PASS before RPO promotion; otherwise marks spectral status pending.
- Adds per-cell resume cache and pre-unblind output tree.
