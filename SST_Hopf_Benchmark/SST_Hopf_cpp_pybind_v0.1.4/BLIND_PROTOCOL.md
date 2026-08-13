# BLIND_PROTOCOL.md — SST Hopf v0.1.4

## Purpose

v0.1.4 separates mathematical/topological discovery from SST comparison.

The blind stage is:

\[
\text{geometry/topology}
\rightarrow
\text{blind observables}
\rightarrow
\text{sealed hashes}
\]

Only after sealing may the reveal stage read SST hypotheses or physical inputs:

\[
\text{sealed blind result}
+
\text{post-seal SST reveal}
\rightarrow
\text{comparison}.
\]

## Non-negotiable blind rules

The blind runner:

1. does not read `private_reveal/`;
2. does not read `sst_reveal.json`;
3. rejects SST/target keys in `blind_config.json`;
4. uses anonymous labels `candidate_A`, `candidate_B`, ...;
5. receives candidate NPZ files containing only `centerline`;
6. records `sst_inputs_used=false`;
7. does not run H6-H8 as blind physical evidence;
8. treats H5 identity and H9 double-cover calculations as self-tests, not SST evidence;
9. is automatically followed by a cryptographic seal when `RUN_BLIND_ALL.cmd` is used.

## Candidate blinding

`PREPARE_BLIND_CAMPAIGN.cmd` creates five normalized candidate centerlines and shuffles their identities.

Public side:

```text
blind_inputs/
  candidate_pack_manifest.json
  candidates/
    candidate_A.npz
    candidate_B.npz
    ...
```

Private side:

```text
private_reveal/
  DO_NOT_OPEN_candidate_key.json
```

The public manifest contains only a SHA-256 commitment to the private key. The blind code never reads the key.

The parametric catalog currently contains an unknot plus four nontrivial knot candidates. Their mapping to anonymous labels is random for each new campaign. Parametric catalog claims are **not independent knot certificates**.

## Blind observables

The blind campaign measures, without SST target values:

- Hopf charge via direct spinor connection;
- Hopf charge via director → fourth-order curvature → Hodge projection;
- gauge residuals;
- preimage linking;
- toroflux regularity/seam residuals;
- anonymous-candidate writhe;
- Bishop-frame twist;
- self-link proxy \(Wr+Tw\);
- normalized arclength;
- radius of gyration;
- nonlocal-distance diagnostic;
- tube spinor/director normalization.

The constructed helicity identity is retained only as:

```text
PIPELINE_SELF_TEST_NOT_PHYSICAL_EVIDENCE
```

The SU(2) \(2\pi/4\pi\) calculation is retained only as:

```text
KINEMATIC_SELF_TEST_NOT_SST_CONFIGURATION_SPACE_EVIDENCE
```

## Gates intentionally not closed blindly

H6 requires an independently reduced physical action.

H7 is conditional on H6.

H8 requires a physical sector-selection rule.

Physical H9 requires a configuration-space/Finkelstein–Rubinstein theorem or certificate.

Particle interpretation in H10 is post-seal reveal material.

## Pre-registered comparison thresholds

`blind_config.json` contains tolerances but **no expected physical target values**.

Default:

```text
STANDARD absolute tolerance   0.05
CERTIFIED absolute tolerance  0.01
```

Changing the thresholds after seeing blind results invalidates that campaign. Start a new campaign instead.

## Seal

`SEAL_BLIND_RESULTS.cmd` hashes:

- blind config;
- candidate manifest;
- source/CMD/C++ code;
- all blind result files.

It creates:

```text
results/blind/SEALED_MANIFEST.json
results/blind/BLIND_RESULT_SHA256.txt
```

Reveal is refused if the blind result tree has changed after the seal.

## Reveal

Only after sealing:

1. copy `sst_reveal.template.json` to `sst_reveal.json`;
2. fill the hypotheses/physical inputs;
3. run `RUN_SST_REVEAL.cmd`.

Possible comparison statuses include:

```text
CERTIFIED_MATCH
MATCH
PARTIAL_MATCH
NO_MATCH
NOT_SPECIFIED
NOT_IDENTIFIABLE_FROM_BLIND_DATA
NOT_IDENTIFIABLE_FROM_BLIND_PHYSICAL_DATA
CATALOG_IDENTIFICATION_ONLY
KINEMATIC_MATCH_ONLY
```

No hidden or missing SST hypothesis is guessed.

## Recommended production workflow

```cmd
RUN_BLIND_ALL.cmd
```

Do **not** inspect `private_reveal/` while it runs.

After `SEALED_MANIFEST.json` exists:

```cmd
copy sst_reveal.template.json sst_reveal.json
notepad sst_reveal.json
RUN_SST_REVEAL.cmd
```

For development-only diagnostics that do not constitute the complete sealed campaign:

```cmd
RUN_BLIND_TOPOLOGY.cmd
RUN_BLIND_CONVERGENCE.cmd
```


## Interpretation guard

Blinding removes target leakage; it does not automatically turn every benchmark into a physical prediction.

In particular, the analytic Hopf benchmark has its topological charge fixed by its mathematical construction. A post-seal agreement between an SST Hopf-charge hypothesis and that benchmark is therefore a **compatibility result**, not a derivation of the SST hypothesis.

For stronger claims, `sst_reveal.json` should record a pre-existing hypothesis source and SHA-256 under `hypothesis_provenance`.
