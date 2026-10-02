# C++17 / pybind11 backend

The backend is adapted directly from the supplied `SST_cpp_pybind_audit_template` architecture: C++ source + pybind module + hash stamp + Python fallback.

## Fast kernels

`cpp/native.cpp` exports:

```text
segment_lengths(points, closed)
biot_savart_velocity(source, evaluation, gamma, core_radius, source_closed)
writhe_midpoint(points, closed)
min_segment_distance(a, b, closed_a, closed_b)
backend_version()
```

The regularized centerline kernel is

\[
\mathbf v(\mathbf x)
=\frac{\Gamma}{4\pi}
\sum_j
\frac{\Delta\boldsymbol\ell_j\times(\mathbf x-\mathbf r_{j+1/2})}
{\left(|\mathbf x-\mathbf r_{j+1/2}|^2+a^2\right)^{3/2}}.
\]

In the default v0.2 encounter workflow, geometry is centered and normalized to `R_rms=1`, `Gamma=1`, and `a/R_rms` is specified by the preset. Therefore the resulting velocity is a **dimensionless coupling proxy**. It must not be reported as an SST physical velocity without an independently fixed geometry scale and circulation normalization.

## Build

```cmd
python -m maxwell_sst_falsifier.native_ext.build_ext_if_needed --force
python -m maxwell_sst_falsifier backend
```

The build hash is stored under `build\maxwell_sst_native.stamp.json`.

## Why threaded runs can accelerate

The C++ loops release the Python GIL. The workflow parallelizes independent encounter configurations with `ThreadPoolExecutor`, so `--threads 16` can execute multiple C++ probes concurrently. The exact speedup is hardware/memory dependent.

## Fallback

`src\maxwell_sst_falsifier\native_ext\fallback.py` implements the same formulas in NumPy/Python. Unit tests always exercise the fallback. The extended CMD requires the native backend to prevent an accidental very slow `N=1200` campaign.
