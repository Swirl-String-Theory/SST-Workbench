# v0.2 implementation status

The original v0.2 roadmap called for a solver-facing mode-extraction layer. This release implements the parts that are physically justified by centerline geometry alone:

- [x] VECT/XYZ/CSV/NPY geometry importer.
- [x] uniform arclength resampling.
- [x] rigid translation/rotation projector.
- [x] centerline-normal Kelvin/shape candidate basis.
- [x] regularized Biot–Savart encounter-response projector.
- [x] writhe response.
- [x] C++ pybind acceleration and Python fallback.
- [x] v0.1 physical campaign skeleton generation.
- [ ] physical Hessian `H` for a declared SST energy functional.
- [ ] generalized inertia/mass operator `M`.
- [ ] true eigenproblem `H e = omega^2 M e`.
- [ ] physical mode-energy transfer and gap extraction.
- [ ] material-frame twist spectrum.
- [ ] finite-core deformation spectrum.

The unchecked items are not silently approximated by geometry proxies.
