# Changelog

## v0.1.3 — Q-breathing / projection-consistency audit fix

This release is a methodological correction driven by the first real `knot_6.3` QHP output audit.

### Critical fixes

1. **Preserve Q breathing.** v0.1.2 independently normalized every candidate to `Rg=1`. That is incompatible with the generator's Q mode, which is a centroid-radial breathing deformation. v0.1.3 uses one common `family_anchor` scale: the reference geometry is normalized once and every candidate in that family/replicate is divided by the same anchor `Rg`. Relative expansion/collapse is therefore retained.
2. **Use one coordinate basis everywhere.** v0.1.2 projected off-axis points onto only the locally available 1-D tangent but the central point onto a 3-D Gram basis. Those coefficients are not directly comparable. v0.1.3 constructs the Q/H/P tangent basis once at the family reference geometry and transports that same basis to every candidate before Gram projection.
3. **Short-time confirmation now requires an actual zero crossing.** A negative `Fshort` slope without a sign change no longer counts as short-time confirmation. The short root must exist, be restoring, and agree with the instantaneous root within the preregistered bracket fraction.
4. **Projection and basis-quality gates apply to line crossings.** A sign reversal in a negligibly coupled or ill-conditioned QHP subspace cannot produce PASS.
5. **3-D confirmation uses both Jacobians.** Instantaneous and short-time Jacobians are both evaluated. Affine fixed-point roots are solved independently and must both lie in the local cell and agree.
6. **Resolution comparison uses confirmed crossings only.** Unconfirmed sign changes no longer contribute to the resolution PASS.

### New diagnostics

- `scale_normalization_mode`
- `candidate_raw_rg`, `family_anchor_raw_rg`, `scale_divisor`
- `basis_condition_number`
- `basis_correlation_condition_number`
- `basis_reference_candidate_id`
- `short_sign_crossing`, `short_root_coordinate`
- `root_disagreement_fraction`
- `projection_qualified`, `basis_qualified`, `confirmed_restoring`
- instantaneous and short-time Jacobian eigenvalues / affine roots

### Compatibility

The C++/pybind11/OpenMP kernel is unchanged from v0.1.2 and retains the MSVC-safe `py::ssize_t` implementation.

## v0.1.2

- metadata integrity hardening;
- reject `geometry_ok=false` before physics;
- hard-fail duplicate file paths and duplicate `(family,replicate,q,h,p)` nodes.
