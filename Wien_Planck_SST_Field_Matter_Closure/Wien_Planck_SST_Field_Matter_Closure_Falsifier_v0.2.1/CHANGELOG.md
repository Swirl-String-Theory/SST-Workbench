# Changelog

## v0.2.1 — strict SST-constant-blind anti-circularity correction

- Removes all SST canonical constants from the pre-reveal Universal Action campaign and scorer.
- Deletes the old `constants.py` and `action_constants.py` pre-reveal modules.
- Adds `reveal_constants.py`, imported only by reveal/provenance code.
- Replaces SI energy extraction with
  \[
  \hat E=\hat S/(8\pi).
  \]
- Replaces `delta_E_J`, `frequency_Hz`, `omega_rad_s` with
  `delta_E_hat`, `frequency_hat`, `omega_hat`.
- Blind normalization is fixed to \(L=1,\Gamma=1\).
- Adds a static `blind_guard` over source, config and blind payload schemas.
- Removes provenance execution from `run_all*.cmd`.
- Makes provenance explicitly reveal-only.
- Splits verdicts into dimensionless universal-action evidence and absolute Planck normalization.
- Adds optional reveal-only independent scale
  \[
  J_0=\rho\Gamma L^3.
  \]
- Legacy SST normalization is supplied only as a reveal-only contaminated negative control.
- Absolute Planck PASS is impossible without an explicitly independent normalization.
- Keeps RK4, \(\Delta t\propto\Delta s^2\), relative-equilibrium, frozen discovery/holdout, amplitude-continuity, temporal/spatial convergence, and blind identity quarantine from v0.2.0.

## v0.2.0

Introduced the integrated Wien–Planck field–matter and Universal Action workbench,
but the action path still used canonical SST values for SI dimensionalization before
blind scoring. v0.2.1 removes that remaining provenance vulnerability.
