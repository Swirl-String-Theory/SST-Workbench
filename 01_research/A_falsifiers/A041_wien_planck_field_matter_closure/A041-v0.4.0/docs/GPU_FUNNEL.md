# GPU qualification funnel — v0.4.0

## Selection is preregistered and target-free

The funnel is intentionally upstream of every action quantity. No \(\Delta\hat E/\hat f\), \(\Delta\hat E/\hat\omega\), target constant, SI scale, or post-reveal parameter is available to Stage 1–3 selection.

### Stage 1 — broad instantaneous screen

Population: all 2352 PKLSA candidates.

Default BASIC resolution: \(N=64\) total centerline points. The dimensionless regularized Biot–Savart velocity is evaluated with the same centerline kernel family as the CPU reference. Candidate deformation is summarized by pair-distance strain RMS. A fixed **top-8 quota per each of 49 families** survives, so a topology cannot disappear merely because another family has many high-scoring variants.

### Stage 2 — short dynamics

Population: 392. BASIC uses \(N=96\) and eight midpoint/RK2 steps. The GPU screen measures rigid-invariant pair-distance signature drift and mesh degradation. A fixed **top-2 quota per family** survives: 98 candidates.

Stage 2 deliberately does not claim temporal convergence, recurrence, relative equilibrium, or an eigenmode. It is only an inexpensive rejection layer.

### Stage 3 — CPU double reference qualification

The 98 survivors are materialized under new opaque filenames and evaluated by the v0.3.1 adaptive-RK4 seed qualification: normal rigid/rolling coherence, short-run Kabsch shape drift, and mesh quality. Final selection is globally score-ranked with a preregistered **maximum one finalist per family**.

### Stage 4 — frozen-mode/action certification

Only Stage-3 finalists enter the v0.3.1 scientific chain: gauge-normal relative equilibrium, independent broadband mode discovery, frozen normal mode, matched perturbation energy/frequency, iterative multi-cycle frequency certification, adaptive reparameterization, temporal convergence, spatial convergence, action-amplitude null and universality gates.

## GPU/CPU trust boundary

The default GPU executable is FP32 SYCL. Before the broad funnel, five deterministic atlas cases spanning different family/component classes are compared against the CPU reference for mean speed, speed CV and pair-strain RMS. The preregistered BASIC relative tolerance is 2%. A parity failure stops the run before selection.

The GPU's driver/device/precision metadata is written into the public funnel record. Candidate IDs and family identities remain in `private_reveal_keys/GPU_FUNNEL_PRIVATE.json` until reveal.

## Why per-family quotas

A pure global top-K would turn the atlas into a competition between topology families and could discard an entire knot class before the trusted CPU stage. Fixed family quotas make Stage 1 and Stage 2 a **shape search within topology**, followed only later by cross-family CPU ranking.
