# E010 / PKLSA v0.3.1 integration — A047 v0.4.0

v0.4.0 retains the fail-closed source-native E010-v0.3.1 contract introduced in v0.3.0. It does not revert to the historical PKLSA-v0.1.1 NPZ bundle.

Authority remains `RELEASE.json`, the `3_1` POC qualification ledgers, carrier envelopes, and original Workbench source bytes. Raw and decoded-geometry hashes are rechecked before dynamics.

The new element is a frozen dependency on the **v0.3.0 BLIND population output**. That parent output supplies anonymous dynamical observables for S00 selection. Selection is written and hashed before `REVEALED/case_reveal_map.json` is opened. The reveal map is then used only to recover the already-selected E010 carriers.

The shipped `data/A047_v0.3.0_PARENT_BLIND_SELECTION_SNAPSHOT.json` documents the selector against the uploaded parent result. It is not used as runtime authority.

Independence groups remain stratification labels. Same-geometry convergence and timestep refinement are the only evidence allowed to satisfy numerical-replication gates.
