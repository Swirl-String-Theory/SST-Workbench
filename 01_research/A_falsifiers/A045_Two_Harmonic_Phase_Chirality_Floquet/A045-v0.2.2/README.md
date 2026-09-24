# SST Two-Harmonic Phase-Chirality Floquet Blind Falsifier v0.2.2

v0.2.2 is a **certification-only hotfix** over v0.2.1.  It does not alter the scientific protocol: finite-core surrogate equations, two-colour drive, frozen A038 seed ensemble, phase/core grids, thresholds, blind salts, and formal-Floquet guard are inherited unchanged.

## Why v0.2.2 exists

A native Windows v0.2.1 basic run completed G1-G7 successfully but G0 reported false leakage hits from two generated artefact classes:

1. `certification/leakage_audit.json`, which necessarily echoed the denylist; and
2. `build/.../native.obj`, a compiler binary that happened to contain a denylist byte sequence.

Those files are not blind scientific inputs or model source.  v0.2.2 makes the G0 audit surface explicit and positive rather than recursively scanning the worktree.

## G0 audit surface

Only these preregistered text classes participate in the leakage gate:

```text
configs/**/*.json
cpp/**/*.{c,cc,cpp,cxx,h,hpp}
sst_thpcf/**/*.py          (except sst_thpcf/provenance.py)
data/FROZEN_INPUTS.json
data/provenance/**/*.json
```

The scanner uses strict UTF-8, records every scanned path, and fails closed when the surface is empty or a selected file cannot be read.  Runtime outputs, `build/`, binary extensions/objects, caches, reveal maps and ZIP archives cannot enter G0 by construction.

## Run

Native basic campaign from a Visual Studio Developer Command Prompt:

```bat
run_build_cpp.cmd
run_all.cmd
```

Extended campaign:

```bat
run_all_extended.cmd
```

Existing outputs remain protected by the non-destructive v0.2.1 allocation policy.

## Scientific status

This remains a blind dimensionless regularized finite-core filament surrogate. `physics_verdict` remains `UNTESTED`, and formal Floquet analysis remains `SKIP_NO_CERTIFIED_RPO` until an independently certified periodic or relative-periodic orbit is supplied upstream.
