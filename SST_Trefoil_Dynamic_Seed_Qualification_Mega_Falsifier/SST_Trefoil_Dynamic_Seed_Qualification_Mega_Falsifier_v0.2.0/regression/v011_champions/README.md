# v0.1.1 champion regression geometries

These five normalized `N=96` geometries are copied from the v0.1.1 BASIC output and are included **only as numerical regression targets**:

- `R5571B55051FC0A.npy`
- `RBA7D30A2A1971D.npy`
- `RBCBB8F3BF914C5.npy`
- `CF6A4B99D7EFC81.npy` (unmodified base candidate)
- `R77732DDD40EE2D.npy`

The v0.1.1 long-run nominees all stopped near `t ~= 0.768` by the old mesh-quality controller before the `t >= 0.8` recurrence window. They therefore do not carry an RPO label.

### v0.2.0 generation-environment regression

For `R5571B55051FC0A`, `N=96`, nominal `dt_factor=0.025`, segment-feedback mesh rate 4.0, no silent timestep coarsening:

- `T=0.9`: `COMPLETED`, max segment-CV `0.2555462521`, max mesh/physical RMS `0.2842477817`.
- `T=1.2`: `COMPLETED`, max segment-CV `0.2776792342`, max mesh/physical RMS `0.4468245752`.

At `T=0.9`, mesh-rate factors 0.6/1.0/1.4 all completed; the largest pairwise parameterization-invariant final-shape distance was approximately `0.01711`, below BASIC's `0.035` mesh-gauge threshold.

These are package-generation regression checks, not a blind physics campaign and not evidence of an RPO.
