# E011-v0.2.0 validation

Validated on 2026-09-26 against the user-supplied:

`E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs.zip`

Input SHA-256:

`b9036620c130b1a2a89b1b0a98c0e088bf2d9b32a661781598806ff40cbfad6b`

## Package tests

- `pytest -q tests`: **10 passed**
- Python modules compile successfully.

## Real E010-v0.3.1 selected-atlas validation

The E010-v0.3.1 parent is structurally valid for selected-subset use, while its global publication gate is intentionally not green under the new literature gates:

- E010 topology universe: 2227
- E010 global failed topologies: 1373
- E010 `full_campaign_gate_pass`: false
- E010 `publication_ready_geometry_layer`: false
- selected E011 scope: 45 topologies
- E011 operational errors: 0

E011 applies the literature hard gates at **carrier level**, not as an all-or-nothing topology rejection. This is essential because many low-crossing topologies contain a large number of good carriers plus a smaller number of failing carriers.

Real selected run result:

- 36 / 45 topologies retain at least one literature-admitted carrier;
- 9 / 45 selected links have no surviving carrier and are excluded (`L4a1`, `L5a1`, `L6a1`–`L6a5`, `L6n1`, `L8a1`);
- 1588 / 1797 carrier rows pass all hard literature gates;
- 209 carrier rows are retained only as exclusion/audit evidence;
- 14 selected topologies support strict cross-provider comparison after mirror/independence guards;
- `8_6` retains only literature-passing mirrors, so E011 emits one provenance-only mirror fallback and does not use it as independent evidence or in consensus;
- execution gate: **PASS**;
- atlas status: **PARTIAL_CARRIER_ADMISSION**.

For `3_1`, 165 carriers survive all hard literature gates while 24 are excluded. This demonstrates why E011 must select carriers rather than discard the entire topology when E010 publication mode reports an aggregate topology failure.

For `8_5`, all six current E010 carriers pass the literature hard gates. E010's independence ledger still identifies the Fremlin/KnotPlot lineage as mirror-related, so E011 does not inflate it into an extra independent provider; Gilbert remains the independent upstream representative for that topology.

## Scientific boundary

This validation establishes software/data-flow correctness for selected geometry/source analysis only. It does not establish dynamical stability, a finite-core vortex solution, Kelvin/Floquet stability, or an SST particle interpretation.
