# v0.2.3.1 probe-output-directory hotfix

Observed:

```text
Stage: probe
[01/20] ... FAIL
...
[20/20] ... FAIL
PROBE PASS=0 FAIL=20
```

Cause:
`generate_kpc.py` writes reload snapshots to `analysis/resume_checks/`, but the
original v0.2.3 package created `analysis/` only. KnotPlot does not create the
missing nested directory when `coords` writes a file, so every probe failed
immediately on output-file creation.

Fix:
- `run_20_probe_100k.cmd` creates `analysis\resume_checks` before launch;
- `run_campaign.py` generically creates parent directories for every declared
  `save` and `coords` destination;
- declared outputs are checked for existence/nonzero size after each run;
- failure details are printed immediately.

Scientific impact: none. All preregistered QHP values, continuation scripts,
source checkpoints, and scientific gates are unchanged.

The failed probes performed no 100k->200k continuation dynamics and are safe to rerun.
