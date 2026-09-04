# v0.2.1 hotfix

Dataset-routing / Windows-CMD fix only.

- Excludes `archive` trees from auto-discovery.
- Fixes exact child exit-code propagation in `run_07_preview_dataset.cmd`.
- Applies the same fix to `run_10_prepare_blind.cmd`.
- Keeps ties between active scientific datasets as hard errors requiring an explicit path.
- Leaves the v0.2.0 preregistration, configs, scientific Python kernels, and C++ kernels unchanged.
