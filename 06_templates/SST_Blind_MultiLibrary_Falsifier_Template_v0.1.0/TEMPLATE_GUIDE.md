# SST Blind Multi-Library Falsifier Template v0.1.0

This is infrastructure, not a physics hypothesis. Its purpose is to stop each new falsifier from re-inventing provenance, blinding, gate ledgers, output security, CPU/GPU authority and statistics.

## Required customization for a new falsifier

1. **Source contract** — what data/libraries are admissible and which are independent provenance families.
2. **Admissibility gates** — topology/geometry/numerical prerequisites that run before outcome scoring.
3. **Discovery statistic** — target-free statistic and null distribution.
4. **Independent confirmation** — held-out or cross-source lane; discovery data cannot confirm itself.
5. **Physical-provider contract** — any expensive solver/mechanism output enters through a versioned, hashed interface.
6. **Private reveal** — historical/experimental targets are stored outside the blind source tree; only their commitment hash is public.

## Fixed infrastructure contract

- C++17/OpenMP/pybind11 reference kernel with explicit setuptools package list.
- Python reference fallback.
- Optional `dpnp` (Intel/SYCL) and CuPy GPU broad screening.
- CPU↔GPU parity before GPU scientific screening.
- CPU-only finalist certification.
- Versioned outputs: `./<Name>_vX.Y.Z-outputs/`.
- Separate `../<Name>_vX.Y.Z-outputs_BLIND.zip` and `*_REVEALED.zip`.
- Gate terminal states: PASS / FAIL / UNRESOLVED / NOT_RUN_PREREQUISITE.

Use `tools/new_falsifier.py` to create a new standalone skeleton.
