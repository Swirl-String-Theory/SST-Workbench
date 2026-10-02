# SST A-Falsifier Instructions

These instructions apply to work under `01_research/A_falsifiers/`.

The purpose of an SST falsifier is to make a hypothesis capable of failing. Scientific independence and provenance take precedence over obtaining agreement with SST.

## Blind / reveal separation

For a blind falsifier, keep the blind phase genuinely blind.

Unless the experimental design explicitly requires them as observable inputs, the blind implementation must not contain or derive from:

- canonical SST target constants,
- known expected target values,
- expected winners,
- expected knot identities,
- preferred ratios,
- desired signs,
- manually chosen tolerances based on the expected answer,
- labels that reveal the expected interpretation,
- or hidden scoring terms that reward agreement with SST.

Do not place target information in:

- blind source code,
- blind configuration,
- filenames consumed by the blind evaluator,
- comments,
- test fixtures,
- thresholds,
- ordering conventions,
- or metadata visible to the blind selection algorithm.

The blind stage should output neutral observables, metrics, candidates, uncertainty estimates, convergence information, and predetermined gate results.

Interpretation against SST belongs in the reveal stage.

## No post-reveal tuning

After a blind result has been revealed:

- do not retune thresholds, weights, filters, resolutions, exclusions, or candidate-selection logic and present the rerun as the same blind experiment;
- do not selectively remove disagreeing candidates without a pre-existing objective rejection rule;
- do not change a gate from FAIL to PASS by weakening the criterion.

If the methodology genuinely needs modification:

1. document why;
2. create a new falsifier version;
3. regenerate the blind configuration;
4. rerun the blind stage;
5. reveal only after the new blind results are fixed.

## Provenance

Each meaningful campaign should preserve enough information to reproduce the result.

Where applicable record:

- falsifier ID and semantic version;
- Git commit or working-tree provenance when available;
- configuration and its SHA-256 hash;
- dataset identity and provenance;
- geometry identity;
- random seed;
- numerical resolution;
- solver and backend;
- compiler/build information for native code;
- tolerances;
- runtime parameters;
- convergence diagnostics;
- rejected cases and rejection reasons.

Do not silently substitute another geometry or dataset when an expected input is missing.

## Gates

Every gate must have:

- a defined observable;
- a mathematical or algorithmic definition;
- a predetermined acceptance criterion;
- a defined treatment of numerical uncertainty;
- a machine-readable result.

Prefer:

`PASS`, `FAIL`, or `INDETERMINATE`

when that distinction is scientifically meaningful.

Do not force numerically unresolved cases into PASS or FAIL.

A gate definition must not depend on knowledge obtained only during reveal.

## Numerical validation

When applicable, check separately:

- spatial convergence;
- temporal convergence;
- solver tolerance sensitivity;
- finite-core or regularization sensitivity;
- geometry-resolution sensitivity;
- Python/native backend consistency.

Do not interpret agreement at one resolution as convergence.

When a result depends materially on a discretization choice, expose that dependence in the output.

## Reference and accelerated implementations

When both Python and C++/pybind11 implementations exist:

- treat the transparent reference definition as the semantic baseline unless the module explicitly documents otherwise;
- verify the native implementation against representative reference cases;
- use tolerances appropriate to the numerical method;
- investigate material disagreement instead of merely widening tolerances.

Performance optimizations must not silently change:
- equations,
- normalization,
- boundary conditions,
- sampling,
- candidate ordering,
- randomization,
- or gate semantics.

## Runs

Implementation work does not automatically authorize a full production campaign.

Unless the user requests the full campaign:

- perform syntax/build checks;
- run unit/regression tests;
- run a small deterministic smoke test;
- use a representative geometry such as the module's documented proof-of-concept case;
- verify that blind and reveal packaging works.

When the user explicitly requests the full campaign, continue through execution, output validation, and repair of failures caused by the implementation.

## Outputs

Preserve the repository's versioned output convention.

Blind artifacts must remain separable from revealed artifacts.

Do not write reveal information back into immutable blind raw results.

Prefer deriving reveal reports from fixed blind outputs rather than recomputing blind metrics during reveal.

Include machine-readable summaries where the existing falsifier architecture supports them.

## Code Review Rules

Flag as a scientific-integrity issue if a change:

- leaks SST target information into a blind stage;
- changes a gate after observing the result without creating a new experimental version;
- introduces circular fitting;
- hides or discards failed samples without a predetermined rule;
- suppresses convergence failures;
- silently changes datasets or geometry provenance;
- mixes blind and revealed outputs;
- modifies historical raw outputs;
- claims scientific validation unsupported by the executed tests;
- changes scientific semantics without an appropriate version increment.

Safe path: preserve the original result, version the methodological change, rerun blind, and reveal from the newly frozen blind output.