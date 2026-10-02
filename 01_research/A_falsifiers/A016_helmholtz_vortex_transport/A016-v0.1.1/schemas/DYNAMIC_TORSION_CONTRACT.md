# Dynamic torsion data required for the rho_f impedance lemma

Static relaxed centerlines are insufficient to test the Core--Torsion Impedance Matching Lemma. A future dynamic extension must provide, independently of the centerline geometry:

- transverse torsion/shear field `A(x,t)` or an equivalent modal representation;
- `partial_t A` and `curl A`, or enough data to reconstruct them;
- translated-core velocity `u` for several small velocities including `u=0`;
- a declared value of `rho_f` and torsion stiffness `K` so `c_T^2=K/rho_f` can be checked;
- field energy reconstructed from the torsion sector, not copied from a target inertia law;
- sufficient orientations to reconstruct the quadratic inertial tensor.

The relevant research-track quantities are

\[
\mathcal L_{\rm torsion}=\frac12\rho_{\!f}|\partial_t\mathbf A|^2-\frac12K|\nabla\times\mathbf A|^2,
\qquad
c_T^2=K/\rho_{\!f},
\qquad
Z_{\rm torsion}=\rho_{\!f}c_T.
\]

These quantities are intentionally **not** inferred from static knot centerlines in v0.1.0.
