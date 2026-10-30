# A011 v0.4.0 - qualified Framework v1.0.10 geometry adapter

Controlled successor of A011-v0.3.1. The predecessor and its results remain intact.
This release adds exact geometry admission, a dedicated adapter to the genuine
v1.0.10 GateLedger, immutable geometry-protocol pins and bounded native/reference
diagnostics. The inherited geometry and kernel definitions are unchanged.

## Run on Windows

Requires CPython 3.14 and numpy/pytest in the tested local environment. The copied
native Windows binary is the byte-pinned v0.3.1 C++17 binary, with its verified
parent build stamp. It intentionally still reports backend 0.3.1-cpp17. The adapter
requires this binary; it never silently rebuilds or substitutes Python fallback.

```bat
py -3.14 -B run_tests_v040.py
run_framework_smoke.cmd
```

The smoke runs one CPU thread, three fixed admitted single-component PKLSA sources
(0_1, 3_1, 4_1) at N=64 and N=128, no random sampling, no GPU, no physical campaign.
The Phase 3 launcher enforces a 120-second subprocess timeout. The source plan is
`config/geometry_smoke_v040.json`; the exact raw and parsed hashes are included.
Carrier selection is defined before execution and does not optimize measured results.

Output is create-once:
`1_Maxwell_SST_Kinetic_Falsifier_v0.4.0-outputs/`. An existing directory is refused;
retain the original output and use a separately reviewed new run/version when needed.
Publication adds the standalone PDF and a sibling result ZIP with SHA-256 sidecar.
`RUN_SUMMARY.json`, `GATE_LEDGER.json`, `SELECTED_SEEDS.json`, parity, environment,
source hashes and resolution deltas are the machine-readable evidence.

## Source qualification and protocol

`.sst_framework_root` selects a content-addressed, separately extracted clean
v1.0.10 CANONICAL_FROZEN distribution. Every one of its 112 manifest entries, and
the complete extracted file inventory, is checked before use. The original local
framework Markdown variant and all old manifests remain preserved.

`FRAMEWORK_SOURCE_PIN.json`, `ADAPTER_INPUT_PINS.json` and
`preregistration/GEOMETRY_PROTOCOL.json` bind the framework, adapter source, input
contracts, selected seeds, loader code, tests and fixed tolerances. Inputs are
rehashed before measurement and again before successful publication. Unknown drift
is an infrastructure failure, never a scientific negative result.

This dedicated geometry runner uses the real v1.0.10 `GateLedger.run_evaluators` and
protocol hashing API. It does not claim to execute the framework's complete
`run_mode` blind/reveal pipeline or its private-target FREEZE procedure. There is
no target comparison or reveal in this tranche.

## Gate meaning and limits

G0/G1: exact software protocol and admitted geometry. G2: finite inherited geometry
diagnostics. G5: measured native/reference parity, attempted despite missing physical
prerequisites; its scientific qualification is DIAGNOSTIC_ONLY. G3/G4/G7/G8 retain
missing-independent-input status. G6 GPU is disabled; G9 reveal is deferred.

The original v0.3.1 tolerances are unchanged: velocity rtol=1e-11, atol=1e-12;
writhe and distance absolute differences <1e-11. Native source coordinate units are
retained. Gamma=1, smoothing=0.05 and the fixed offset in the kernel comparison are
nondimensional software probes, not independently calibrated physical inputs.
Two resolutions expose sensitivity; they do not establish convergence.

No energy spectrum, physical thermodynamic closure, gravity, Euler/Casimir mechanism
or SST prediction is certified. Physical execution still requires independent
energies/gaps, relaxation/couplings, sampled state counts, calibrated source units,
held-out pressure/force evidence and appropriate convergence. No threshold is fitted
to an expected answer. Historical negative findings are not imported as new evidence.

The former release documentation and source manifest are retained under
`provenance/PARENT_*`. Legacy physical workflows remain inherited for reference;
they are outside this release's controlled smoke command and were not run here.
