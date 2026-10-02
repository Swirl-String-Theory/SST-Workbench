# Changelog

## v0.1.1 — seed-identity / overwrite integrity hotfix

- **Critical:** QHP `family` is now the unique source-seed identity, e.g. `knot_6.3`, `link_6.3.1`, `link_6.3.2`, rather than the ambiguous numeric class `6.3`.
- Adds descriptive `topology_class` and `seed_kind` columns without using them to merge manifolds.
- Prevents output-file collisions before any write.
- Adds a strict audit for duplicate metadata paths, missing files, and families containing multiple seed hashes.
- Adds `--clean-output` with a safety guard; it only replaces an empty directory or a directory carrying a recognized QHP generator summary.
- `run_*.cmd` now regenerate cleanly by default.
- `run_focus_6p3.cmd` now targets specifically `knot_6.3`, not unrelated `link_6.3.*` seeds.
- No change to Q/H/P geometric basis definitions or perturbation amplitudes.
