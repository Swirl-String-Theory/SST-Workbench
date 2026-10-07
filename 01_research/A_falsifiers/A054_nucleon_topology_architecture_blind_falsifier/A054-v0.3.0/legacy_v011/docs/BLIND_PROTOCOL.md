# Blind protocol v0.1.1

The blind phase receives only anonymous three-component geometry arrays, fixed numerical settings and anonymous circulation sectors `Q0`--`Q7`. It receives no skeleton name, `5_2`/`6_1` label, composition interpretation, nucleon label, PKLSA provider identity, mass target, charge target, atomic observable or SST canonical constant.

`tools/build_blind_runner.py` exports only:

- `blind.py`
- `blind_geometry.py`
- `physics.py`
- `seal.py`
- an optional compiled `_native` backend

A semantic leak scan is committed in `RUNNER_MANIFEST.json`.

Prepare commits `_private/PRIVATE_MAPPING.json` by SHA-256 before blind execution. Blind seals:

- `BLIND_MANIFEST.json`
- `BLIND_RESULTS.json`
- `ANALYSIS_BLIND.json`
- `REPORT_BLIND.md`
- `BACKEND_QUALIFICATION.json`
- the exact blind config SHA-256
- the private-map commitment

Reveal verifies those commitments and **does not recompute observables**.

The geometry itself can in principle be reverse-engineered by a determined human. The claim is therefore operational/code-level blinding, not information-theoretic secrecy.

## Prospective polarity rule

The v0.1.0 polarity effect is explicitly classified as discovery evidence. The v0.1.1 gate is frozen before v0.1.1 reveal and uses only sign/direction conditions, not an effect size fitted to v0.1.0.

## Status semantics

- `NUMERICALLY_QUALIFIED`: numerical qualification only.
- `INCONCLUSIVE_NUMERICAL`: convergence/objectivity/backend/finite-integration qualification failed.
- sector `QUALIFIED_SHORT_HORIZON`: frozen short-horizon shape/link gates passed.
- sector `FAIL_SHORT_HORIZON`: one or more short-horizon gates failed.
- `polarity.both_normalizations_gate`: prospective polarity criterion passed in both normalization sectors.
- `PREPARED_PARTIAL_FAIL_CLOSED`: full upstream factor set absent; production inference forbidden.

No weighted winner score is used.
