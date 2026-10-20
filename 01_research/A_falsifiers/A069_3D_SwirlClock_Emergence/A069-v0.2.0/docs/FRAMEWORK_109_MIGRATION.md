# v1.0.7 -> v1.0.9 migration audit

Official Drive sources (2026-10-17) report v1.0.9 derived via v1.0.8, with no change in scientific gates, thresholds, scientific models or C++/SYCL/DD32 kernels.

New: unique run IDs, nonoverwriting archive outputs; immutable `SCIENCE_EVIDENCE_MANIFEST.json`, separate final `OUTPUT_MANIFEST.json`, portable newline-normalized diagnostic hash (byte exact authoritative), robust A4 PDF tables, `REPORT_ONLY` without output-tree mutation and reveal evidence preflight.

Validation record: 72/72 Python tests Linux 3.13; 99/99 parent manifest hashes; Windows Arc A770 hardware parity pending. The shipped v1.0.9 minimal.toml retains a `[framework] version = "1.0.7"` label from the predecessor: this metadata is not a source pin, and the present instance pins its true root and project.version separately; do not silently modify the frozen framework.

The scientific A069 G2/G3 analytic results of v0.1.0 are inherited controls and separately regenerated; they are not automatically upgraded to independent physical evidence.
