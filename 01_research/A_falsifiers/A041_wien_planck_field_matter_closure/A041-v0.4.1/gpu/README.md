# PKLSA-2352 GPU qualification backend

This backend is **screening-only**. It performs dimensionless regularized Biot–Savart evaluations over the broad PKLSA population and a short RK2 shape/mesh screen. It cannot issue a final Wien–Planck/Universal-Action PASS.

Default scientific path:

1. 2352 PKLSA candidates -> SYCL FP32 instantaneous strain screen.
2. fixed per-family quota -> SYCL FP32 short-dynamics invariant-shape screen.
3. survivors -> CPU double C++/pybind11 seed qualification.
4. distinct-family CPU finalists -> v0.3.1-derived frozen-mode/action certification.

The runner performs CPU↔GPU parity before the full funnel. GPU device, vendor, driver, precision and kernel/source seal are logged. If GPU is unavailable, use `run_all_cpu_fallback.cmd`; that path is scientifically valid but can be much slower and is explicitly labelled as CPU fallback.
