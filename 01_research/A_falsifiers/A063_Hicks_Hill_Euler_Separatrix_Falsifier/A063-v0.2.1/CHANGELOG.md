# A063 — changelog

## v0.2.1 — exact invariant surfaces, 15 October 2026

- **New S0–S11 gate family**; all gates continue after FAIL.
- Parent A063 v0.2.0 evidence imported in a byte-hashed, immutable baseline; previous scientific gate decisions are not modified or promoted.
- Reproduce numerically closed T(3,4) streamline; directly calculate its streamfunction value.
- Construct three regular meridional streamfunction contours and their surfaces of revolution, with mesh-size refinement and explicit sampled isotopy to a standard torus.
- Check independent finite-difference normals against analytic velocity; infer vorticity tangency from the exact Beltrami relation.
- Correctly distinguish the **knot carried on an unknotted torus boundary** from a **knotted solid-torus core**. The latter hypothesis for the psi-level construction FAILS.
- Preserve separation of field-line winding shear from genuine time-dependent Euler instability.
- Rebuild standalone LaTeX and PDF report automatically, with three graphs and full gate table; no migration of framework v1.0.7 is performed.
- Python automated regression suite: 17 PASSED.
- Clarify limitations: no 3D Euler perturbation solver, no C++ certification, no E013 independent replication.
