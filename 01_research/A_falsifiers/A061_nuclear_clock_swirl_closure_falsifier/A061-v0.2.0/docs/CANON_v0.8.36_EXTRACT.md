# Canon-v0.8.36 extract -- source-priority for A061 v0.2.0

Canonical reference: [SST_CANON-v0.8.36.pdf](https://drive.google.com/file/d/15n8i5dWzHSGA72fU4LZoryRrj7BF3n9n/view), O. Iskandarani (13 Aug 2026), DOI 10.5281/zenodo.21922231.

**Provenance:** Human-readable transcription of mathematical claims and epistemic labels from source, not a claim of first-principles confirmation. This instance never replaces the canonical PDF.

- Sect. 3.10 Eq. (94): `S_t[A;T] = d tau_A/dT = sqrt(1-u_A(T)^2/c^2)`, with **u_A meaning declared per observable**.
- Eq. (95): internal fixed swirl-speed diagnostic is a special case only, not translational Lorentz dilation.
- Sect. 3.11: `v_swirl = 1.09384563e6 m/s` is distinct from `c = 299792458 m/s`; do NOT substitute v_swirl for c.
- Sect. 3.14 Eq. (107): `D(R^2 omega)/Dt=0` conditional on the material-loop and near-solid-body assumptions. Eq. (110) is a horn-anchored special transport identity, not an unrestricted vortex-thickness law.
- Sect. 4.6 Eq. (151): circulation delay `tau_circ(K)=L_K/v_swirl` is a constitutive kinematic proposal.
- Sect. 4.8: stable matter and radiation must share the same effective causal cone (monometricity; open theorem target).
- Sect. 10.4-10.9: classical `omega_mode > 0` is not equivalent to a positive excitation **energy gap**. Required simultaneous gate: coupling nonzero, drive threshold and response time.
- Sect. 11.4: action-phase mass-shell clock `H=hypot(P*c,E0)`, `d tau/dT = E0/H`, `Omega/Omega0 = E0/H` at specified fixed momentum.
- Appendix Q.3 Eq. (852): `dot(theta)=omega_K + epsilon*f(t)*sin(omega_drive*t - theta)` and conditional locking `|omega_drive-omega_K| <= epsilon*|f0|` (research-track).
- SpectroResponseAPI: `nu=Delta E/h`, `delta nu=delta(Delta E)/h`; a null frequency ratio needs an independent two-species transfer coefficient.

**Scientific separation:** historical SST-28 uses speed-normalized `sqrt(1-(v_perp/v_swirl)^2)`. That expression is retained strictly as a different candidate/legacy model, not silently equated with Canon Eq. (94).

**No Z6 claim:** Canon v0.8.36 does not establish a sixfold vortex-particle symmetry. Cheon et al. and Gao et al. concern magnetic NiPS3 clock models and furnish comparison/negative-control physics only.
