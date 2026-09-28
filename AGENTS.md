# SST-Workbench Instructions

## Repository purpose

SST-Workbench is a research and scientific-software repository for Swirl-String Theory (SST), numerical falsification, knot and link geometry, finite-core vortex models, stability analysis, and supporting scientific tooling.

Treat scientific provenance, reproducibility, falsifiability, and separation between hypotheses and evidence as first-class requirements.

## Repository source of truth

For repository organization and catalog work:

- `family_hierarchy.json` is authoritative for research-family hierarchy and naming.
- `catalog_index.json` is authoritative for catalog identifiers, versions, and canonical repository locations.
- Consult these files when a task changes a catalog ID, family, version, canonical path, migration, or registry entry.
- Do not assume remembered paths, historical folder layouts, or old ZIP contents are current when the repository contains newer canonical metadata.
- Do not rename, move, or reclassify registered research artifacts without updating the corresponding canonical indices and references.

For SST scientific definitions:

- Current SST Canon and Rosetta material in the repository is authoritative for SST-specific definitions, notation, classifications, and canonical constants.
- Do not silently replace an SST definition with its GR, QFT, classical-fluid, or other mainstream analogue.
- Mainstream physics is the comparison/reference framework unless the task explicitly states otherwise.
- When Canon, Rosetta, implementation, and experimental results disagree, report the discrepancy rather than silently choosing whichever produces the desired result.

## Scientific status

Keep the following categories distinct:

- **Orthodox:** established external mathematics, physics, numerical analysis, or experimentally supported results.
- **Derived:** results mathematically or numerically derived from explicitly stated SST assumptions.
- **Speculative:** hypotheses, mappings, interpretations, conjectures, or unvalidated proposed mechanisms.

Do not promote a speculative result to derived or established status because it is numerically suggestive.

Do not describe a falsifier as confirming SST merely because a gate passes. State precisely what hypothesis, metric, or condition survived the test.

## Numerical and physical requirements

For scientific calculations:

- Use SI units unless another system is explicitly required.
- Check dimensional consistency for new or modified formulas.
- State important assumptions.
- Check analytically known limits where applicable.
- Check relevant numerical convergence where practical.
- Distinguish discretization error, temporal error, solver tolerance, fitting error, and physical-model uncertainty when they are relevant.
- Do not hide NaN, Inf, solver divergence, failed convergence, missing samples, or rejected geometries.
- Never replace a failed scientific gate with a warning merely to obtain a passing campaign.

When comparing SST against established physics, preserve the distinction between:
1. externally established equations or measurements,
2. SST assumptions,
3. derived predictions,
4. fitted quantities,
5. numerical observations.

## Canonical notation

When SST canonical notation is required, preserve the notation defined by the current Canon/Rosetta.

Do not casually rename canonical variables or introduce duplicate symbols for an existing quantity.

When producing LaTeX scientific material:

- use explicit, dimensionally meaningful equations;
- define every nonstandard symbol;
- preserve canonical SST notation;
- include bibliographic provenance for non-original external equations, methods, or comparisons when the artifact requires scientific references.

## Research integrity

- Never tune a model toward a known target and then describe the resulting agreement as an independent prediction.
- Identify fitted parameters explicitly.
- Identify parameters imported from external measurements explicitly.
- Preserve negative and null results.
- Do not delete failed runs because they weaken a hypothesis.
- Do not modify historical raw results when creating a new interpretation; create a new derived artifact or version instead.
- Version scientifically meaningful changes.

## Code and workflow

Respect the implementation pattern already used by the affected research module.

When a module uses the Python/C++ falsifier pattern:

- keep Python as a transparent reference or orchestration implementation where applicable;
- use C++/pybind11 for performance-critical kernels when the module already uses that architecture;
- keep C++ and Python outputs cross-checkable;
- do not make native acceleration silently change the mathematical definition of a metric.

For Python packaging:

- keep package discovery explicit when non-package directories such as `cpp/`, `configs/`, datasets, or generated outputs coexist with Python packages;
- avoid accidental setuptools auto-discovery of those directories.

For Windows-first research modules:

- preserve working `run_all.cmd` orchestration when the module uses it;
- do not replace it with a Unix-only workflow unless explicitly requested;
- keep commands usable from the repository's documented Windows development environment.

## Validation strategy

For local changes:

1. run the narrowest relevant unit or regression tests;
2. run a representative smoke test;
3. compare important Python/native results when both implementations exist;
4. inspect generated summaries and machine-readable outputs;
5. run a full production campaign only when explicitly requested or when the task specifically requires it.

A full knot-library campaign, high-resolution Biot-Savart run, long Floquet campaign, or equivalent expensive computation is not implied by a request to implement or patch the code.

## Generated research outputs

When an existing falsifier follows the standard SST output convention, preserve it.

Preferred structure:

`./<FalsifierName>_vX.Y.Z-outputs/`

and archive:

`../<FalsifierName>_vX.Y.Z-outputs.zip`

For blind/reveal workflows, preserve separate artifacts such as:

- `*_BLIND.zip`
- `*_REVEALED.zip`

Do not mix raw source geometry with derived campaign outputs.

Preserve where applicable:

- configuration,
- configuration hash,
- software/falsifier version,
- backend,
- random seed,
- dataset provenance,
- timestamps,
- numerical resolution,
- tolerances,
- convergence information,
- and environment/build metadata.

## Versioning

A new version is required when a change can alter scientific conclusions, metrics, gates, datasets, numerical algorithms, canonical inputs, or reveal logic.

Pure packaging, documentation, or execution fixes may use a patch version when they do not alter scientific semantics.

Do not overwrite an older scientifically meaningful version merely because a newer implementation exists.

## Completion criteria

For a requested research-software change, continue until the requested tranche is:

- implemented,
- executable,
- minimally validated,
- inspected for scientific/provenance regressions,
- and documented sufficiently for the next reproducible run.

Report what was actually tested. Never imply that an unexecuted production campaign was executed.