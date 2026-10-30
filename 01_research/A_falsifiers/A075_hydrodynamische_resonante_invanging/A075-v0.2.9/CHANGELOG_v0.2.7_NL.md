# A075-v0.2.8 — Gate, Source & Boundary Qualification

**Parent:** A075-v0.2.6. **Framework:** authentic embedded 1.1.0, unchanged.
**Release class:** DEVELOPMENT_ONLY / scientific UNRESOLVED.

- G5 and G6 are enabled independent from G4. Each runs **two real right-hand-side Euler operator comparisons** on analytic knot inputs `0_1` and `3_1`: compiled C++/pybind11 FP64 and genuine Torch XPU FP32 versus Python/SciPy FP64. Only limited numerical operator parity is eligible for PASS; the full trajectory is independently checked by the mandatory framework backend matrix. No device simulation or CPU fallback.
- G7 is enabled independent from G6; it remains UNRESOLVED until original `5_2`/`6_1` XYZ inputs and independent topology verification are available. Byte hashes alone do not certify knot identity.
- G1 now tests actual Workbench-relative paths, source existence and equality to the **expected** SHA-256 for A021/A032 methodological README files and the local Euler solver. Their independence is not claimed.
- G10 is added: **optional** same-physical-`dx` three-box periodic-image sensitivity. A diagnostic execution PASS is **not** a free-space / open-boundary qualification. Full physical G8 remains UNRESOLVED.
- Default BASIC, EXTENDED and FULL keep the previous periodical Fourier–Galerkin Euler method and adaptive timesteps. `--domain-study` opt-in; `--domain-study-only` runs in an explicitly standalone *non-framework-qualified* diagnostic destination so it does not invent a two-of-three science gate result.
- Retained heartbeat and per-iteration energy conservation matrices.
- No change to pinned framework runtime files or the earlier BLIND data. **Do not reuse v0.2.6 private keys/frozen registrations.**

## Scientific limitations

The model remains periodic, and there is no verified source exit, independently validated receiver clock, 100-cycle retention, finite-core convergence, open-boundary/free-space solution or independent unseen holdout. The two-level RHS checks use intentionally small numerical test grids and are not Euler continuum-certification.
