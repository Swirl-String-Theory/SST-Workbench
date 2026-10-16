# A058-v0.2.6 validation — shared safe-seed repair

## Cause and fix

The user's Windows KnotPlot installation declared the unmodified catalogue trefoil after `load 3.1; refine nbeads 300` unsafe under Damped + `collision fast` defaults. This is a scale/separation admissibility failure, not a scientific null result. Version 0.2.6 preregisters **one** geometry-scale normalization at install: `fitto mindist (1.05 × runtime close default)`. It does **not** set or change `close`, `max-dr`, `stusplit`, `timeincr`, collision policy, or any force default. The normalized seed is saved in exactly one ASCII export, reloaded, and checked for safety before and after `go 1`. The SHA-256 of the immutable seed is bound into the campaign manifest, runtime manifest, condition runlogs and G1 provenance gate. Each of the 271 scientific conditions loads the same seed without refining or fitting.

**Scientific scope qualification:** The initial absolute embedding scale is no longer the original catalogue geometry scale. Although this scale is the same for all conditions, it can affect force magnitudes and trajectories; therefore v0.2.6 does not claim scale invariance or a globally unique attractor. If geometric normalization cannot create a safe reload, installation deliberately fails closed.

## Isolated validations performed

- 31/31 Python package/unit tests PASS using the local mirror of Framework v1.0.8 contracts, including two mock KnotPlot install-integration tests (successful safe-reload, deliberate unsafe failure).
- Mock install -> campaign generation produced **271** conditions: 6 references + 1 R2-OFF control + 8 × 33 perturbations, with one shared-seed hash in the manifest.
- Exactly one shared ASCII trefoil export is registered for the install test; no `ago 1000`, no second export during reload/go-one liveness.
- Framework-v1.0.8 science/source/gate/report validators all returned [] (PASS).
- Framework blind scan: 0 forbidden-term hits; nonced blind terms and reveal commitments: PASS.
- Isolated Framework-v1.0.8 FREEZE and frozen verification: PASS. Protocol SHA-256 on simulation copy: `488a6dc586f88247262a2a7c4ce3e56bdf71e03cfd80c6f3ef345f6da364e249`.
- LaTeX report compiled successfully with pdflatex (3 pages, isolated temporary build).
- Release contamination scan: 0 hits, no cached/compiled artifacts, private run logs, or output trees in released source.
- Source ZIP checked for exact manifest checksums and ZIP CRC integrity.

## Target-only validations still pending

- **The actual KnotPlot.exe Windows build was not executed here.** The `fitto mindist` command is based on the user's existing historical KnotPlot script; correctness of its safe target must be confirmed by the install log on that build.
- Actual Windows MSVC C++/pybind11 compilation, KnotPlot + collision kernel, adaptive 271-condition dynamics, scientific gate outcomes and PDF publication via the target framework remain unverified.
- Framework v1.0.8 is the user's `LOCAL_VALIDATED_CANDIDATE`, built on v1.0.7 frozen parent; no independent backend certification is claimed here.

## Target commands

```bat
cmd.exe /c run_install.cmd
cmd.exe /c run_pilot_all.cmd
```

Inspect `private/install_test_runtime/trefoil_install_test.log` and `private/install_test_runtime/shared_safe_seed.json` if the seed preflight still fails. Previous v0.2.5 provenance is retained unchanged.
