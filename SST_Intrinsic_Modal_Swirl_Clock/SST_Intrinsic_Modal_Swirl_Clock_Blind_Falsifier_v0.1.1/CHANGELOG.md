# Changelog

## v0.1.1 — 2026-08-27 — Long-horizon recurrence certification

- BASIC observation horizon increased from `T_final=1.2` to `12.0`.
- EXTENDED increased from `2.4` to `24.0`.
- Focus campaigns and the N=64/96/128 resolution ladder use `T_final=18.0`.
- BASIC now requires at least 2 holdout cycles; EXTENDED 4; focus/resolution 3.
- Increased stored sample budgets for long-window recurrence/phase-space analysis.
- Increased `max_steps` budgets to preserve the existing `dt ~ ds^2` integration policy over the longer horizon.
- **Numerical safety:** the solver now hard-fails if `max_steps` would be exceeded. It never silently enlarges the timestep.
- No change to Biot-Savart physics, material-core law, blind identities, POD discovery/holdout split, stretch-delay test, or fixed-core null. This release isolates the effect of longer observation.

## v0.1.0 — 2026-08-27
- Initial intrinsic-modal swirl-clock falsifier after the QHP stability-landscape campaign.
- Defaults to `..\..\KnotPlot\knots\final` relaxed centerlines.
- Broadband normal `+/-` probe instead of hand-selected Q/H/P coordinates.
- Discovery/holdout POD/SVD split with frozen spatial modes.
- Material-core vs fixed-core null.
- Recurrence, stretch-to-modal-acceleration measured-delay and phase-scramble gates.
- Focus scripts for `knot_6.3`, `link_4.2.1`, and `link_9.2.20`.
- Windows/MSVC native source uses only `py::ssize_t`; regression guard included.
