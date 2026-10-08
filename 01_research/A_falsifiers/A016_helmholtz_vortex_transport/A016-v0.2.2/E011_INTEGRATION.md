# E011-v0.3.0 STATIC_READY integration contract

A016-v0.2.2 consumes the falsifier-facing E011/SKLSA static seed atlas rather than requiring a hypothetical E010-v0.4.0 publication-ready release.

## Canonical dependency

```text
01_research/E_pipelines/E011_sklsa_selected_knot_link_seed_atlas/E011-v0.3.0/
  E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs/
```

If the unpacked output directory is absent, A016 may use the canonical `...v0.3.0-outputs.zip` archive when uniquely resolvable.

## Why E011 is authoritative here

E010-v0.3.1 is a broad production qualification campaign whose global publication-ready flag is false. E011-v0.3.0 explicitly consumes E010-v0.3.1 and exports the subset that is `STATIC_READY` for downstream static geometry falsifiers. A016 therefore validates both E011 and the required E010 parent gates, but it does not demand E010 global publication readiness.

## Source integrity

Every admitted seed must be upstream-independent, `STATIC_READY`, and `PRIMARY_REFERENCE`. A016 verifies the raw source SHA-256 before numerical work. Supported representations:

- `xyz`: strict XYZ text parser;
- `vect`: strict Geomview VECT parser;
- `gilbert_ab_record`: exact Gilbert catalogue record selected by topology/reference ID and sampled from Fourier coefficients.

For Gilbert records the immutable catalogue SHA-256 plus record identity is the cross-platform provenance gate. Sampled geometry SHA-256 is retained as E011 identity metadata but is not recomputed as a hard gate because platform/libm LSB differences can alter sampled floating-point bytes.

## Replication policy

FULL uses one deterministic E011 provider anchor per topology/provider. CERTIFY uses all primary STATIC_READY carriers so within-provider A016 classification dispersion is visible. X0 still gives each provider exactly one vote.
