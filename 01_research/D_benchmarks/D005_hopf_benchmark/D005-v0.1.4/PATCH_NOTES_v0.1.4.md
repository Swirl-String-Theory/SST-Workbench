# v0.1.4 Patch Notes — Blind Falsification Infrastructure

## Research change

v0.1.4 does not add a new SST physical assumption. It changes the experiment architecture.

The blind stage is deliberately unable to read SST target values or the anonymous-candidate identity mapping. The result is frozen before reveal.

## Added

- `blind_config.json`
- `BLIND_PROTOCOL.md`
- `blind_utils.py`
- `prepare_blind_campaign.py`
- `run_blind_candidates.py`
- `run_blind_campaign.py`
- `run_blind_convergence.py`
- `seal_blind_results.py`
- `run_sst_reveal.py`
- `sst_reveal.template.json`
- seven new Windows CMD entry points

## Blind candidate pack

A fresh campaign generates five normalized candidate centerlines with random label assignment:

```text
candidate_A ... candidate_E
```

The blind files contain only coordinates. The identity key is stored under `private_reveal/` and committed by SHA-256 before the run.

The catalog generator claims are not independent knot certificates.

## Evidence classes

Counted as blind evidence:

- H0-H4;
- direct and director/Hodge Hopf observables;
- gauge/linking residuals;
- anonymous geometry/topology observables.

Excluded from physical blind evidence:

- H5 constructed identity benchmark;
- H9 SU(2) double-cover self-test.

Not run as blind physical closure:

- H6-H8;
- particle interpretation in H10.

## Seal/reveal

`RUN_BLIND_ALL.cmd` seals automatically. Reveal refuses modified blind result trees or a candidate key that does not match the pre-seal commitment.

## Ordinary runner fix

`run_all.py` now wires upstream evidence into H10, and step 8 accepts multiple spin-evidence sources.
