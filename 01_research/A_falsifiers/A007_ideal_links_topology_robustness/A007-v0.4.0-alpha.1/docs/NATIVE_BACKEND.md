# Native backend contract

## Exported C++ kernels

`cpp/native.cpp` exports:

```text
velocity_at_points(evaluation_points, source_points, gamma, epsilon, same_curve, local_skip)
link_velocity_batch(curves, sign_matrix, epsilon, local_skip)
gauss_linking_matrix(curves)
neumann_coupling_matrices(curves, epsilons, local_skip)
build_info()
```

The batched velocity output is one array per target component, with shape

```text
(number_of_sign_sectors, number_of_target_points, 3)
```

so the source-segment integrals are reused across every circulation assignment.

## Build provenance

The builder hashes `cpp/native.cpp` and records the digest in
`build/sst_link_native.stamp.json`. It searches for pybind11 headers in this order:

1. installed `pybind11` package;
2. scientific distributions that vendor the standard headers, such as PyTorch;
3. system include directories.

The release ZIP intentionally contains no compiled `.pyd` or `.so`; a binary must be built for the local Python ABI and platform.

## Fallback policy

- exploratory commands may fall back to NumPy;
- production campaigns should pass `--require-native`;
- `--force-python` exists for independent reference runs;
- `--require-native` and `--force-python` are mutually exclusive;
- native parity failure stops the campaign before link outputs are produced.
