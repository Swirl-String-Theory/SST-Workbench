# Native backend contract — v0.3.3

## Exported C++ kernels

`cpp/native.cpp` exports both the legacy segment-count interface and the continuum-safe fixed-arc
interface:

```text
velocity_at_points(evaluation_points, source_points, gamma, epsilon, same_curve, local_skip)
link_velocity_batch(curves, sign_matrix, epsilon, local_skip)
link_velocity_batch_arc_exclusion(curves, sign_matrix, epsilon, exclusion_arc)
gauss_linking_matrix(curves)
neumann_coupling_matrices(curves, epsilons, local_skip)
neumann_coupling_matrices_arc_exclusion(curves, epsilons, exclusion_arc)
build_info()
```

The batched velocity output is one array per target component, with shape

```text
(number_of_sign_sectors, number_of_target_points, 3)
```

so source-segment integrals are reused across circulation assignments.

## Fixed-arc semantics

Each polygon component is assigned cumulative arclength coordinates.  For self interactions, the
minimal cyclic arclength between an evaluation vertex/segment midpoint and a source-segment midpoint
is used.  The interaction is omitted when

\[
\Delta s_{\rm cyc}\le s_{\rm excl}.
\]

This keeps the physical exclusion window fixed as N changes.  The QM presets specify the exclusion in
units of the Gilbert diameter D and convert to absolute source coordinates before entering the native
kernel.

## Build provenance

The builder hashes `cpp/native.cpp` and records the digest in `build/sst_link_native.stamp.json`.  The
release ZIP intentionally contains no compiled `.pyd` or `.so`; build locally for the active Python
ABI and platform.

## Fallback and parity policy

- exploratory commands may use the NumPy reference backend;
- production campaigns should pass `--require-native`;
- `--force-python` exists for independent reference runs;
- native parity covers legacy and fixed-arc velocity/Neumann kernels;
- native parity failure stops the campaign.
