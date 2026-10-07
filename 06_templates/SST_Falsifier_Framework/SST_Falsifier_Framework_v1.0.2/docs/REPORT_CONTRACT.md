# Falsifier report contract

`report/FALSIFIER_REPORT.tex` is a scientific protocol, not cosmetic documentation.

## Freeze rule

`FREEZE` hashes the exact TeX source together with `science_contract.json`, `source_contract.json`, `gate_plan.json`, `falsifier.toml`, `blind_policy.json`, and the public nonced commitment of the private forbidden-term list. A later change causes `CERTIFY` to stop. A scientific change therefore requires a new version/campaign.

## Machine/human dual description

`science_contract.json` is machine-checkable and maps equations to algorithmic steps and gates. The TeX report provides the rationale, derivations, assumptions, dimensional checks and interpretation. `AUTO_SCIENCE_CONTRACT.tex` is generated from the JSON so discrepancies are visible in the compiled report.

## Result insertion

Run outputs create `AUTO_RESULTS.tex`. It contains protocol hash, environment, gate ledger, backend manifest and source manifest. The frozen report uses `\IfFileExists` to include this generated file without mutating preregistered scientific text.

## Certification requirement

The report validator rejects `\SSTTODO{...}`, `REPLACE_BEFORE_FREEZE`, `TODO_SCIENCE`, or missing required section markers before a strict freeze/certification run.

## Post-run narrative

`POST_RUN_DISCUSSION.tex` is deliberately outside the frozen protocol. Use the provided template only after the blind run; the frozen report includes it conditionally.

## Reveal verification

`FREEZE` commits both the private reveal payload and the private forbidden-term list using a private nonce. `REVEAL` verifies both commitments before copying the reveal payload, nonce and opaque-ID key into the revealed output package.

## Reveal phase separation

`REVEAL` never reruns the scientific pipeline. It consumes the frozen protocol and the existing blind FULL/CERTIFY ledger. By default G3 must already be PASS or FAIL and no pre-reveal gate may remain UNRESOLVED. The policy can be tightened in `blind_policy.json`, but weakening it requires a new frozen campaign.
