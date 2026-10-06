# Producer input/output contract

The evaluator consumes one JSON manifest. Every physical case must contain immutable provenance plus a time-series record.

Minimal shape:

```json
{
  "schema": "A053-PRODUCER-v1",
  "blind": true,
  "producer": {
    "name": "...",
    "version": "...",
    "physics_class": "finite_core_reconnection",
    "target_aware_reconnection": false
  },
  "cases": [
    {
      "case_id": "opaque-id",
      "hypothesis": "H2",
      "source_group": "opaque-source",
      "resolution": 128,
      "circulation_sector": "fixed_total_equal_split_same_sign",
      "sham": false,
      "time": [0.0, 0.1],
      "component_count": [2, 2],
      "abs_linking": [1.0, 1.0],
      "energy": [1.0, 1.0],
      "helicity": [0.5, 0.5],
      "phase12": [0.0, 0.1],
      "phase_weight": [1.0, 1.0],
      "interaction_mask": [0, 1],
      "reconnection_events": []
    }
  ]
}
```

`phase12` and `phase_weight` may be omitted for H0/H2/H3. They are mandatory for a physical H1 PASS.

`reconnection_events` records event time, local separation, core-scale criterion, and rule identifier. A requested/target topology field is prohibited.
