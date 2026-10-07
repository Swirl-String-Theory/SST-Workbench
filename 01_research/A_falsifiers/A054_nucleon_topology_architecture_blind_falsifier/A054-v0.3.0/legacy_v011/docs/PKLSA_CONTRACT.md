# PKLSA / SKLSA handoff — v0.1.1

Runtime authority is local `E010-v0.3.1` + `E011-v0.3.0`; bundled snapshots are documentation only.

Required seed contracts:

```yaml
- topology_id: 5_2
  require_static_ready: true
  provider_policy: every_provider_anchor
- topology_id: 6_1
  require_static_ready: true
  provider_policy: every_provider_anchor
```

Every `5_2` provider anchor is crossed with every `6_1` provider anchor. The same anchor realization is used wherever that topology appears repeatedly inside a three-component factor cell, preserving the v0.1.0 provider-envelope semantics.

Known upstream state entering this release:

- `5_2`: cross-provider robust;
- `6_1`: static-ready but cross-provider sensitive.

Therefore `6_1` conclusions remain provider-conditional unless sign/effect direction survives the complete provider envelope.

`L6a4` is audited but is not treated as production static-ready Borromean geometry in this campaign. `B` is an analytic generated closed-braid skeleton. `G` is an analytic `T(3,3)` topology proxy.

For linked decorated cells, each skeleton component is locally connected-summed with its assigned PKLSA knot inside a sampled disjoint insertion ball. Preparation fails closed if sampled clearance or pairwise skeleton-link preservation fails. Exact isotopy/polynomial certification remains a later gate.
