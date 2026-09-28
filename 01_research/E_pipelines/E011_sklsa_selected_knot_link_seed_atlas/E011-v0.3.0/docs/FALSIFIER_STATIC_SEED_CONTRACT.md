# E011 v0.3.0 — Static seed contract for SST falsifiers

A downstream falsifier must request seed properties; it must not silently choose a convenient geometry file.

Minimum request:

```yaml
seed_contract:
  topology_id: 3_1
  require_static_ready: true
  required_capabilities:
    - writhe_ready
    - acn_ready
  minimum_independent_providers: 2
```

Recommended execution policy:

- `CROSS_PROVIDER_ROBUST`: run at least the provider anchors from every independent provider and propagate `PROVIDER_AGREEMENT` / uncertainty envelopes.
- `CROSS_PROVIDER_SENSITIVE`: run every provider anchor; conclusions must remain provider-conditional unless they survive the envelope.
- `SINGLE_PROVIDER_QUALIFIED`: static falsification is allowed, but the result must be labelled single-provider evidence.
- `STATIC_NOT_READY_*`: do not use the topology for a production static falsifier unless the falsifier explicitly studies the failed/negative-control condition.

Capabilities are observable-specific. For example, a ropelength test must request `ropelength_ready`; `STATIC_READY` alone does not imply that every optional observable is numerically resolved.

Provider anchors are deterministic convenience representatives. The atlas also retains every primary `STATIC_READY` carrier, and provider agreement is computed from provider medians across those carriers rather than from the anchors. Therefore an anchor choice cannot manufacture provider agreement.

`STATIC_READY` does not imply `DYNAMICS_READY`.
