# B007 v0.2.3 change log

- Add `run_all.cmd ATLAS` paired E010 T(2,3) perturbation experiments, retaining existing v0.2.2 CLI.
- Consume 121 source-verified analytic perturbed records at N2048 and N4096 directly from directories or ZIPs.
- Fail closed on manifest/hash/generator/config/provenance mismatch or missing selected B0.
- Reconstruct nominal analytically; independently evolve nominal vs perturbed under regularized filament Heun integrator.
- SE(3) Kabsch align at sampled times; export amplification, return candidate, shape and length drift.
- Compare two temporal refinements and two spatial levels separately; preserve heuristic resolution checks.
- Create-only run folders with CSV, JSON, Markdown, PDF and ZIP/SHA-256.
- Do not certify physical stability, chaotic behavior, full field Euler, topology, or finite-core reach.
