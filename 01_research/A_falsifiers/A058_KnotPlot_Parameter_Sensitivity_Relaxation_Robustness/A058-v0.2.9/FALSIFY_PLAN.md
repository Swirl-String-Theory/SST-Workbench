# A058 v0.2.9 preregistered execution plan

**Hypothesis:** slider perturbations may measurably alter finite-time trefoil shape, scale-free scalars and bead spacing relative to sector-default references. We do not test asymptotic stability at a fixed time.

- 6 active sector references + 1 R2 OFF activation control + 8×33 strength levels = 271 registered conditions.
- All conditions reload the same SAFE shared trefoil; collision fast; Damped. Geometry scale is normalized once during install.
- BASIC 512: checkpoints `32, 128, 512`, all 271.
- 2048: checkpoints `32, 128, 512, 2048`, all 271.
- HEAVY 32768: checkpoints `32, 128, 512, 2048, 8192, 32768`, no more than 31.
- Heavy selection is *before* any heavy analysis: prefer 2048, otherwise BASIC; include successful references/activation control; per axis select highest-scoring k±1 local response, highest overall finite-time score, and zero/endpoint robustness point, with deterministic duplicate fill. Score = 0.7 Dshape + 0.3 max relative scalar deviation. The hashes, chosen IDs and justification are immutable within the run tree.
- Any sector with broken KnotPlot process or unconfirmed counter is quarantined, not silently imputed. Try graphics-initialized mode for drag only as a qualified compatibility fallback.
- Reference/sweep shapes only compared after identical numbers of KnotPlot iterations. Scientific gates explicitly distinguish finite-time evidence and convergence claims.
- Retain independent output trees by budget, framework ZIP/PDF artifacts by run ID. G0–G9 semantics are unchanged.
