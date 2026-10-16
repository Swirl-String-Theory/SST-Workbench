# Framework v1.0.7 handoff

This package uses the installed, unchanged CANONICAL_FROZEN v1.0.7 generator and runner, never a copied or reimplemented framework. Run `run_all.cmd FRAMEWORK` on the user's Workbench system. The local execution environment used to prepare the release does not contain the physical framework directory; `FRAMEWORK_STATUS.json` therefore records the local status rather than claiming a completed native run. The program selects the genuine frozen root using `CANONICAL_FREEZE.json`, freezes a new instance, then runs FULL and REVEAL_IF_ALLOWED. The physical-source G3 is UNRESOLVED by design. A PDF with the same version/identity is always produced independently of LaTeX availability after any controlled blind run.

A new scientific version is required if the physical prerequisites or protocol change; do not mutate an already frozen native instance.
