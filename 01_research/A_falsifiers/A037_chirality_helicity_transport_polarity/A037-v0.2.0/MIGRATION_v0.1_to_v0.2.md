# Migration notes: v0.1.0 -> v0.2.0

Do **not** compare v0.1 and v0.2 `transport_pi` numerically as if they were the same observable.

- v0.1 `transport_pi`: late-time Fourier handedness from a frozen transverse Jacobian.
- v0.2 `transport_pi`: dynamically generated spatial packet-energy asymmetry along an evolving baseline trajectory, with initial offset removed.

The v0.2 classification is intentionally harder to pass. In particular, a candidate with a large mirror-odd response is still `INDETERMINATE` when its base geometry is not sufficiently close to a relative equilibrium, when shape/mesh drift is excessive, or when tangent/rigid/amplification contamination dominates.

For links, v0.1 positive results should be considered superseded because its flattened loader could insert nonphysical connector segments. v0.2 either recovers explicit components or rejects the ambiguous source.
