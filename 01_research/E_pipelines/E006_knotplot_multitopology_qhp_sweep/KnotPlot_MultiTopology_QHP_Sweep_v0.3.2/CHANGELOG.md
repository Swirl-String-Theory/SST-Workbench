# v0.3.2.3

Cumulative v0.3.2.x release.

Includes the previous:
- live timer / ETA and staged panels;
- explicit synthetic 0.n.1 unlink controls;
- `keep component` extraction for real multi-component links;
- length-proportional component bead allocation.

New fix:
- checkpoint resume is now metric-neutral;
- removed `centre` and `fitto mindist` from the post-load resume path;
- no refinement is performed on resume;
- a pre-resume probe compares checkpoint length/Rg with the reloaded state;
- continuation aborts before any further `ago` if relative length or Rg differs
  by more than 2e-5.

Uninterrupted runs are unchanged.
