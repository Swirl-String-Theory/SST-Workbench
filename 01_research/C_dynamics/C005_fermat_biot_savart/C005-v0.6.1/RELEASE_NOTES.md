# v0.6.1 — Full-range hole-bundle audit

## Requested parameter domain

\[
0.06125\le R_b/R_{\rm hole}\le 8,
\qquad
-8\le \Gamma_h/\Gamma_0\le 8.
\]

The default full grid contains 42 unique radius ratios and 65 circulation ratios, for 2730 combinations.

## Scientific correction

The primary stabilization metric is now the reduction of the absolute residual norm after fitting the best rigid translation and rotation. The previous relative residual is retained only as a secondary diagnostic. This prevents an artificially large rigid velocity from masquerading as shape stabilization.

## Added

- generated log/linear radius grids with exact endpoints and anchor values;
- generated circulation grids with exact endpoints, fixed step, and mandatory zero controls;
- vectorized analytic hole-bundle field and Jacobian;
- reusable rigid-motion least-squares projector;
- centerline clock-validity flag;
- selected-candidate centerline convergence audit;
- axis-offset and axis-tilt robustness audit;
- Fourier residual-mode projection;
- shared finest-level field cache;
- integrated campaign summary and provenance manifest;
- per-file and archive SHA-256 checksums;
- resumable full campaign launcher.

## Not claimed

The bundle is axially periodic, not a finite closed vortex loop in unbounded space. No relative equilibrium, global Fermat orbit, monodromy spectrum, QSM, or physical proper-time law is certified.
