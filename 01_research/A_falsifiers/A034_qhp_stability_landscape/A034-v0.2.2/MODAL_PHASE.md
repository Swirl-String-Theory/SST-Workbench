# A034-v0.2.2 modal-phase bridge

Additive curvature-proxy export. The parent CAMPAIGN gate, `soft_tol`, and `ENERGETICALLY_ADMISSIBLE` rule are unchanged. Historical parent fields remain `{g, H, C_constraint}` and `tangent_hessian_eigenvalues` only for provenance.

`modal_bridge.py` writes the constrained curvature proxy `C = P H_parent P` and the exact restricted operators `C_j = P_j C P_j`. It does not certify dynamic stability or a physical energy Hessian (`dynamic_stability_claim: false`, `physical_energy_hessian_claim: false`).
