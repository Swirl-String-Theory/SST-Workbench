# A057 Master-Mass Reconstruction Blind Falsifier v0.2.0

**Framework:** SST Falsifier Framework v1.0.6 `CANONICAL_FROZEN`  
**Cross campaign:** E013 PKLSA Cross-Falsifier Campaign v0.1.1  
**Carrier authority:** E011 SKLSA v0.3.0 `STATIC_READY` provider anchors frozen by E013.

## Scientific reset

v0.2.0 deliberately does **not** import scientific results from A057-v0.1.2 or any other
legacy falsifier. It reuses methods/code only. The numerical evidence is recomputed from the
exact current carrier identities supplied in:

```text
%SST_CROSS_CARRIER_MANIFEST%
```

Required manifest schema:

```text
E013-COMMON-CARRIER-MANIFEST-1
```

Every admitted carrier is bound to:

```text
topology_id
static_seed_id
carrier_id
provider_group
geometry_sha256
source_locator
```

A057 then reloads the source-native geometry bytes through the E010-v0.3.1 parser and verifies
the frozen raw/geometry hashes before science continues.

## Main change from v0.1.2

The primary question is no longer whether an arbitrary E010 discovery set supports a mass
kernel. It is whether **one shared E013 carrier population** supports the A057 finite-core
energy/dynamics chain.

The dynamical authority is also stricter. A source geometry is promoted to a local stability
candidate only when

\[
\sigma_{\rm stat}
=
\frac{\|\nabla U\|}{\max(|U|,\epsilon)}
\le \sigma_{\max}.
\]

Frozen thresholds:

- BASIC: `0.10`
- FULL: `0.05`
- CERTIFY: `0.01`

A nonstationary carrier still receives Hessian/Jacobian diagnostics, but its spectrum is labeled
`DIAGNOSTIC_NONSTATIONARY` and cannot close the spectral-ratio stability gate.

## Diagnostic continuation

Only protocol/implementation integrity is hard. Scientific FAIL/UNRESOLVED states do not
suppress later diagnostics. This preserves negative evidence while preventing unsupported
promotion.

## Intended run path

Normally E013 launches A057:

```bat
run_all_cross_falsifier.cmd BASIC C:\workspace\projects\SST-Workbench
run_all_cross_falsifier.cmd FULL C:\workspace\projects\SST-Workbench
run_all_cross_falsifier.cmd CERTIFY C:\workspace\projects\SST-Workbench
```

For direct debugging you may pass the E013 manifest explicitly as the third argument:

```bat
run_all.cmd BASIC C:\workspace\projects\SST-Workbench C:\path\to\CROSS_CARRIER_MANIFEST.json
```

Before first execution:

```bat
run_00_install.cmd
run_all.cmd FREEZE
```

## Key outputs

- `E013_CAMPAIGN_BINDING.json`
- `A057_SOURCE_ADMISSION.json`
- `A057_CARRIER_RESULTS.jsonl`
- `A057_TOPOLOGY_SUMMARY.json`
- `A057_DYNAMIC_RESULTS.jsonl`
- `A057_MODEL_COMPETITION.json`
- `PREDICTIONS_FROZEN.json`
- `DEPENDENCY_CAVEATS.json`
- framework provenance, gate ledger and output manifests.

`E013_CAMPAIGN_BINDING.json` records the exact common-carrier-manifest SHA-256 so later
cross-falsifier joins can prove that every member used the same carrier population.
