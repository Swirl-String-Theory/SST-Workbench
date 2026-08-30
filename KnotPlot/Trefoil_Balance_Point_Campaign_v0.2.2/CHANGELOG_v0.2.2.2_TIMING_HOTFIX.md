# v0.2.2.2 timing hotfix

Observed:

```text
[01/20] DONE K31__Q01 PASS ...
KeyError: 'elapsed'
```

Cause:
- `one()` stores runtime in `elapsed_seconds`;
- the outer campaign loop read `r["elapsed"]`.

Fix:
- the loop now reads `elapsed_seconds`;
- missing-prerequisite failures use the same field name;
- ETA bookkeeping uses `dict.get()` defensively.

Scientific impact: none.

The successful Q01 probe may safely be repeated; probe runs only reload and
measure the 60k checkpoint.

Unchanged:
- balance_design.json
- PREREGISTRATION.md
- PREREGISTRATION_LOCK.json
- all 20 q/h/p points
- all continuation KPCs
- all scientific gates
- all 60k source states
