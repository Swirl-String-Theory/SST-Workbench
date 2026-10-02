# KnotPlot MultiTopology QHP v0.3.2.4 metrics-recovery/runtime hotfix

This patch addresses the observed KnotPlot Windows log sequence:

```text
*** unknown data field `s'
*** no data format set!
0 data records written
```

The completed `.k float` checkpoint states are preserved and are sufficient to
recover the scientific length/Rg/E analysis without rerunning the dynamics.

## Existing Stage-1 campaign

Overlay this ZIP on the MultiTopology QHP project root, then run:

```bat
run_recover_stage1_screen_30k_v2.cmd
```

or for another campaign:

```bat
run_recover_campaign.cmd campaign_name
```

The recovery:
- validates every expected `.k` checkpoint;
- parses all `LOCF` chunks directly from KnotPlot binary float states;
- uses total closed component arclength for `L`;
- uses a global bead-weighted radius of gyration for `Rg`;
- computes the original E surrogate and inherited late gates;
- backs up the old `analysis/REPORT.*`;
- replaces it with a recovered report;
- never invents the unavailable `/s` safeness field.

## Future campaign generator hotfix

Run once:

```bat
apply_v0324_runtime_hotfix.cmd
```

It searches project source/template KPC text outside `campaigns/` and replaces:

```text
data format "/I,/l,/g,/N,/s"
```

with:

```text
data format "/I,/l,/g,/N"
```

and removes `safeness` from the corresponding CSV header.

Backups are written with `.pre_v0324`.

For scientific post-analysis, saved `.k` states should remain the authoritative
geometry source, especially for multi-component links.
