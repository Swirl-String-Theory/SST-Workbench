# CHANGELOG

## v0.2.2

- Certification-only hotfix over v0.2.1; scientific model, configs, blind salts, frozen seeds, gates, thresholds, and native equations are unchanged.
- Replaces the recursive all-file G0 leakage scan with an explicit positive allowlist of blind scientific source/config/provenance payloads.
- Build products (`build/`, `*.obj`, `*.pyd`), runtime outputs/certification files, reveal data, archives, and caches are excluded by construction rather than by fragile path substring tests.
- Excludes `sst_thpcf/provenance.py` from self-audit because it contains the denylist by definition.
- G0 now fails closed if the allowlisted surface is empty or any allowlisted file cannot be read as strict UTF-8.
- `leakage_audit.json` records the policy, source globs, exact exclusions, scanned-file inventory, and read errors.
- Adds regression tests reproducing both v0.2.1 false-positive classes and a positive-control forbidden-token failure.

## v0.2.1

- Execution-robustness patch; scientific model, configs, blind salts, gates, frozen seeds, and thresholds are unchanged from v0.2.0.
- Removes destructive `shutil.rmtree()` cleanup of prior output directories.
- Uses the canonical output directory only when it is absent; otherwise allocates a unique `_RUN_<UTC+PID>` sibling.
- Stores reveal maps per run under `private_reveal/reveal_maps/` instead of overwriting one fixed reveal map.
- Never overwrites an existing BLIND/REVEALED output ZIP; repeated packaging receives a run-suffixed archive name.
- Adds explicit tests for non-destructive output and archive allocation.

## v0.2.0

- Adds frozen A038 trefoil seed ensemble with SHA-256 fail-closed admission.
- Freezes E010/PKLSA and A038 provenance artifacts.
- Replaces the v0.1.0 LIA reference evolution with a regularized nonlocal finite-core segment model.
- Rewrites the two-colour drive as an explicit planar waveform followed by a covariant trace-free strain map.
- Adds core-radius/mesh ladder support and temporal refinement certification.
- Separates `numerics_verdict` from `physics_verdict`.
- Keeps formal Floquet analysis at `SKIP_NO_CERTIFIED_RPO`.
