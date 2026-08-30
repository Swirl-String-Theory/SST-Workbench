# Validation — v0.2.2

Artifact-side validation passed:

- design selftest PASS;
- preregistration lock PASS;
- 20/20 q/h/p settings exactly identical to v0.2.1;
- generated exactly 20 reload probes and 20 continuations;
- KPC audit confirms no `fitto`, `refine`, or `centre` before the first resumed `ago`;
- continuation checkpoints are exactly 70k,80k,90k,100k;
- source importer successfully read the supplied repaired v0.2.1 60k outputs ZIP;
- importer requires only history <=60k plus all 20 `i60000.k` states;
- 60k continuity-verifier code path exercised with identity reload snapshots: PASS;
- actual KnotPlot 60k->100k dynamics must run on the Windows target.
