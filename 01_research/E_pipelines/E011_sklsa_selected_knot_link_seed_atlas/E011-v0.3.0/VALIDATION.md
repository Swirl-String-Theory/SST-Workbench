# E011 SKLSA v0.3.0 validation

Validated against `E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs.zip`

Parent SHA-256: `b9036620c130b1a2a89b1b0a98c0e088bf2d9b32a661781598806ff40cbfad6b`

## Software gates

- pytest: **14 passed**
- compileall: **PASS**
- real selected run: **PASS**
- operational errors: **0**

## Real selected run

- selected topologies: **45**
- E010 carrier-admitted topologies: **36**
- STATIC_READY topologies: **34**
- primary STATIC_READY carriers: **431**
- provider anchors: **47**
- control STATIC_READY carriers: **455**
- cross-provider robust: **9**
- cross-provider sensitive: **4**
- single-provider qualified: **21**

### CROSS_PROVIDER_ROBUST

`3_1, 5_1, 5_2, 6_2, 7_1, 7_2, 7_3, 7_4, 8_1`

### CROSS_PROVIDER_SENSITIVE

- `4_1`: Wr_abs:between_provider_relative_span=1.99231>0.15
- `6_1`: Wr_abs:between_provider_relative_span=0.190476>0.15
- `8_17`: Wr_abs:between_provider_relative_span=1.77408>0.15; kappa_rms:between_provider_relative_span=0.192787>0.15; dcsd:between_provider_relative_span=0.343124>0.3
- `8_18`: Wr_abs:between_provider_relative_span=1.98236>0.15; kappa_rms:between_provider_relative_span=0.177902>0.15; dcsd:between_provider_relative_span=0.308832>0.3

### Not STATIC_READY

- `8_3` — `STATIC_NOT_READY_CORE_OBSERVABLES`: Wr:not_RESOLVED
- `8_6` — `STATIC_NOT_READY_MIRROR_ONLY`: no_independent_upstream_primary_seed, mirror_never_static_ready
- `L4a1` — `STATIC_NOT_READY_E010_EXCLUDED`: EXCLUDED_NO_LITERATURE_ADMITTED_CARRIER
- `L5a1` — `STATIC_NOT_READY_E010_EXCLUDED`: EXCLUDED_NO_LITERATURE_ADMITTED_CARRIER
- `L6a1` — `STATIC_NOT_READY_E010_EXCLUDED`: EXCLUDED_NO_LITERATURE_ADMITTED_CARRIER
- `L6a2` — `STATIC_NOT_READY_E010_EXCLUDED`: EXCLUDED_NO_LITERATURE_ADMITTED_CARRIER
- `L6a3` — `STATIC_NOT_READY_E010_EXCLUDED`: EXCLUDED_NO_LITERATURE_ADMITTED_CARRIER
- `L6a4` — `STATIC_NOT_READY_E010_EXCLUDED`: EXCLUDED_NO_LITERATURE_ADMITTED_CARRIER
- `L6a5` — `STATIC_NOT_READY_E010_EXCLUDED`: EXCLUDED_NO_LITERATURE_ADMITTED_CARRIER
- `L6n1` — `STATIC_NOT_READY_E010_EXCLUDED`: EXCLUDED_NO_LITERATURE_ADMITTED_CARRIER
- `L8a1` — `STATIC_NOT_READY_E010_EXCLUDED`: EXCLUDED_NO_LITERATURE_ADMITTED_CARRIER

## Provenance audit

- primary seed geometry-hash locators: **431/431 complete**
- provider-anchor geometry-hash locators: **47/47 complete**
- unique primary static seed IDs: **431/431**

Provider agreement uses **provider medians**, not individual-carrier vote counts. Within-provider dispersion remains in `PROVIDER_AGREEMENT.json`; `UNCERTAINTY_ENVELOPES.csv` exposes the flattened uncertainty layer. Provider anchors are convenience representatives and do not determine agreement.

`STATIC_READY` remains explicitly distinct from `DYNAMICS_READY`.
