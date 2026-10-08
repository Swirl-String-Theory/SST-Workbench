# A057 Master-Mass Reconstruction Blind Falsifier v0.1.2

**Framework:** SST Falsifier Framework v1.0.6 `CANONICAL_FROZEN`  
**Profile:** `multilibrary_gpu`  
**Mode:** blind, fail-closed for protocol/integrity, **diagnostic-continuation for scientific gates**.

A057 asks whether the historical SST/VAM mass-factorization can be reconstructed from source-native PKLSA geometry through a finite-core reduced Hamiltonian, its self/mutual coherence matrix, a reduced Lagrangian/Hamiltonian pair, and Hessian/Jacobian spectra. Observed target masses and protected historical numerical targets are unavailable during BLIND.

## Important gate semantics

This instance deliberately distinguishes **hard dependencies** from **soft scientific dependencies**.

- `G0` protocol/integrity is the only hard prerequisite.
- Every scientific gate `G1..G8,G10..G22` depends only on `G0` in the framework DAG.
- A scientific `FAIL` therefore **does not prevent later gates from running**.
- `experiment/pipeline.py` catches gate-local numerical/source exceptions, records `UNRESOLVED`, and continues.
- `DEPENDENCY_CAVEATS.json` records which failed/unresolved earlier results weaken interpretation of each later result.
- `G9` remains the framework-owned commitment-verified reveal gate.
- Reveal does **not** require all scientific gates to pass, but `G17` must be evaluable (`PASS` or `FAIL`) so a frozen prediction table exists; `G17=UNRESOLVED` cannot unlock reveal.

Thus, for example, a nonstationary carrier may fail the reduced-action stationarity test while still yielding an explicitly caveated Hessian/Jacobian diagnostic. A source-family replication failure does not erase a numerically interesting carrier-specific spectrum.

## Run

```bat
run_00_install.cmd
run_all.cmd FREEZE
run_all.cmd BASIC C:\workspace\projects\SST-Workbench
run_all.cmd FULL C:\workspace\projects\SST-Workbench
run_all.cmd CERTIFY C:\workspace\projects\SST-Workbench
run_all.cmd REVEAL_IF_ALLOWED
run_post_reveal_analysis.cmd
```

Convenience wrappers are also supplied: `run_basic.cmd`, `run_full.cmd`, `run_certify.cmd`. The optional second argument of `run_all.cmd` (or first argument of the convenience wrapper) sets `SST_WORKBENCH_ROOT`; when omitted the canonical `C:\workspace\projects\SST-Workbench` default is used.

`FULL` and `CERTIFY` are the scientific blind campaigns. `BASIC` is an architecture/diagnostic smoke run and cannot unlock reveal.

## Main outputs

Inside `Master_Mass_Reconstruction_Blind_Falsifier_v0.1.2-outputs/`:

- `A057_CARRIER_RESULTS.jsonl`
- `A057_TOPOLOGY_SUMMARY.json`
- `A057_DYNAMIC_RESULTS.jsonl`
- `A057_MODEL_COMPETITION.json`
- `PREDICTIONS_FROZEN.json`
- `DEPENDENCY_CAVEATS.json`
- framework `GATE_LEDGER.json`, provenance, source and backend manifests.

The protected comparison is performed only after framework reveal and writes to a **separate sibling post-reveal directory**, so the framework-hashed revealed output tree is not mutated.

## v0.1.2 integrity preflight

`run_00_install.cmd` now finishes by executing `python -m master_mass.commitment --verify`. A digest mismatch therefore fails during installation instead of first appearing at G0 in BASIC/FULL/CERTIFY.
