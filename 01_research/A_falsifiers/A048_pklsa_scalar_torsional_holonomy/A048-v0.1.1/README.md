# A048 PKLSA Scalar–Torsional Holonomy v0.1.1

Status: **SYNTHETIC_DISCRIMINATOR_QUALIFIED**. Physical hypothesis: **INDETERMINATE / NOT_YET_TESTED**.

This additive patch keeps v0.1.0 byte-identical and repairs its demonstrated blind-integrity and classification defects. The complete 74-item backlog is machine-readable in GATE_STATUS_MATRIX.json; prior conversation claims are preserved separately in docs/SOURCE_CHECKLIST.md.

Build with `python setup.py build_ext --inplace`, then run `python run_pipeline.py`. Use `--python-only` when intentionally qualifying just the reference backend. Every invocation creates a unique, immutable run. Individual stage commands require `--run-dir`.

Output parent: `../A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier_v0.1.1-outputs/`. Each child identifies falsifier, version, suite, UTC timestamp and random ID. ZIPs retain the same run prefix and end in `_BLIND.zip`, `_REVEALED.zip`, `_outputs.zip`. No previous run is deleted. Test/build logs have their own run identities.

The synthetic comparison is one pure Kelvin-like curve versus one pure torsional-like curve, with absolute relative-RMS adequacy <= 0.05 and minimum delta-AIC 6. It is not a joint H0 versus H1 physical branch test. Missing phase observations are INDETERMINATE, not a negative scientific result.

See docs/CYCLE_EVALUATION.md, docs/PROVENANCE.md and docs/BLIND_PROTOCOL.md for limitations and evidence.
