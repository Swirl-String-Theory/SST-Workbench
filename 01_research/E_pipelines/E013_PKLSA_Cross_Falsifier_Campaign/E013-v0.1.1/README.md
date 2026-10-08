# E013 PKLSA Cross-Falsifier Requalification Campaign v0.1.1

Hotfix/re-numbered successor to the initial prototype.

Key corrections:
- canonical pipeline ID is E013, not E011;
- carrier authority is E011 SKLSA v0.3.0 `STATIC_READY_PROVIDER_ANCHORS.jsonl`;
- E013 no longer scrapes E010 `geometry_metrics.jsonl` directly;
- PLAN/FULL never demand three providers when E011 only certifies one or two;
- optional unavailable links are recorded instead of aborting the campaign;
- PLAN/BASIC return `READY_NO_MEMBERS` when no downstream falsifier has opted in yet.

## Run

```bat
run_all_cross_falsifier.cmd PLAN C:\workspace\projects\SST-Workbench
run_all_cross_falsifier.cmd BASIC C:\workspace\projects\SST-Workbench
run_all_cross_falsifier.cmd FULL C:\workspace\projects\SST-Workbench
run_all_cross_falsifier.cmd CERTIFY C:\workspace\projects\SST-Workbench
```

The expected current E011-v0.3.0 situation is roughly:
- `3_1`, `5_2`, `6_1`, `4_1`: STATIC_READY with two provider anchors;
- `L2a1`: STATIC_READY with one provider anchor;
- `5_1`, `6_2`: available extended controls;
- `L4a1`, `L6a4`: not STATIC_READY in E011-v0.3.0 and therefore explicitly NOT RUN;
- `0_1`: not supplied as a STATIC_READY requested topology in that atlas.

No substitute geometry is silently introduced.
