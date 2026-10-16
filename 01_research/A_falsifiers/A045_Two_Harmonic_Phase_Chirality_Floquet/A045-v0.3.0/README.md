# A045 v0.3.0 — PKLSA / upstream RPO / Floquet audit bridge

**Important:** This is an additive import + independent qualification verifier, NOT a new finite-core PDE solver and NOT an automatic source of RPOs. Original A045 v0.2.2 G0-G7 remain unchanged and must still pass independent native parity + extended core ladder. It corrects no physics by itself.

`run_all.cmd SELFTEST`: synthetic implementation checks (not physical evidence)

`run_all.cmd SEARCH --trajectory C:\path\E011_dynamic_trajectory.npz`: candidate scan only; `times` array plus `positions` of shape (frames,points,3), 16+ points. Uses SO(3)+translations and sampled cyclic shifts to find approximate relative return. **This scan is a candidate generator, never RPO certification.**

`run_all.cmd CHECK --rpo C:\path\RPO.npz`: geometric RPO closure only

`run_all.cmd CERTIFY --rpo C:\path\RPO.npz --meta C:\path\RPO.provenance.json`: validate upstream attestation and if supplied, a full-state tangent map.

**NPZ contract:** arrays `x0`, `xT` shape (n,3), `rotation` shape (3,3) proper orthogonal; scalar `shift_points` integer, optional `translation` shape (3,) (default zero), optional full-state `monodromy` shape (3n,3n). `xT = roll(x0,shift_points) @ rotation.T` defines the group action; the relative monodromy is `S^{-1}M` where M is an independent lab-frame full tangent map.

**Upstream provenance example:**
```
{
 "source_sha256":"<sha256 of RPO.npz>","source_class":"A031_RPO",
 "certified_rpo":true,"held_out":true,"independence_group":"independent_hashed_source",
 "blind_commitment_verified":true,"full_tangent":true,
 "neutral_multiplicities_verified":2,
 "convergence":{"closure_refined":1e-5,"timestep_ratio":2,"mesh_refined":1e-3,"tangent_fd_parity":1e-4}
}
```
Metadata fields are **upstream claims**, not independently audited simply because the JSON says true. Existing framework seals/source contracts must independently authenticate them. The use of a low-dimensional full-state test fixture is not equivalent to the 600-/1200-point PKLSA carrier, and the reference eigensolver intentionally guards against impractically large systems. `PASS_LINEAR_MODEL` never means nonlinear or physical stability.

For full Floquet campaigns, connect to an independently certified RPO of A031/A038 or finite-core Euler provider, with accepted source hashes, symmetry mode and tangent-map parity. If none, `G5=NOT_RUN` and `physics_verdict=UNTESTED` is correct.
