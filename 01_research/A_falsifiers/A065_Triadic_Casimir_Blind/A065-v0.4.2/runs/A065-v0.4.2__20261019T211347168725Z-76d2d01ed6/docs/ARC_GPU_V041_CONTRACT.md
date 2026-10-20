# GPU Euler scientific contract — v0.4.1

All numeric tolerances are frozen in `preregistration/ARC_GPU_V041.json` before
running the A003 GPU. GPU FP32 is numerical screening, not independent physics.

Comparison: exact same CPU-initialized, projected u0 is passed to GPU FP32 and
NumPy FP64; independent FFT/RK4 operation but not independent physical source.
Measure relative L2 over full u, omega, and p fields. Thresholds: u <= 1e-3,
omega <= 3e-3, numerical pressure <= 1e-2. Divergence RMS <= 1e-4.
These thresholds are software screening choices, not fitted physical targets.
No GPU fallback; output records full device and classifies missing data.

This extension does not claim oneMKL C++ standalone FFT implementation; it uses
Intel dpnp FFT on the selected SYCL Level Zero device. `dpnp`'s FFT backend
is Intel optimized in compatible installations but actual backend/driver
provenance must be recorded and validated on target machine.

Original D01/D02/D03 and all historical G0-G42 are append-only and unchanged.
