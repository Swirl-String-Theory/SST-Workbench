# Changelog

## v0.1.2.4 — detector floor + eigenpair canonicalization

- Replaces raw `Re(lambda)` sign-crossing promotion with resolved `|Re(lambda)|` growth-floor transitions; effective floor `max(1e-8, eps_machine/(h/a))`.
- Counts both-endpoints-sub-floor sign flips as rejected numerical diagnostics instead of candidates.
- Requires fixed dominant `|m|` identity across a growth-transition bracket and across branch-local `|lambda|` minima.
- Canonicalizes conjugate and +/- eigenvalue partners before convergence clustering.
- Canonicalizes conjugate C4 residue sectors `r` and `-r mod 4` for the same physical `|m|` family.
- Uniqueness gate now operates on canonical physical events rather than raw eigenbranches.
- Quick campaigns report unavailable full-ladder gates as `"not_evaluated"`; full promotion still requires all gates to be exactly `true`.
- Adds detector diagnostics, synthetic detector/eigenpair regressions, quick-gate semantics regression, and `DETECTOR_PROTOCOL.md`.
- Adds `reprocess_detector.py` / `run_reprocess_quick_research.cmd` to apply the new detector to stored v0.1.2.3 Fourier rows without recomputing the operator.
- No finite-core kernel, Fourier projection, C4 leakage gate, or external-target logic changes.

## v0.1.2.3 — Windows native runtime loader hotfix

- No scientific/numerical model changes.
- Activates MinGW/Strawberry runtime DLL directories with `os.add_dll_directory()` before importing `_native`.
- Stores compiler runtime DLL directories in the native build stamp.
- Adds `-static-libgcc -static-libstdc++` on Windows to reduce runtime dependencies.
- `run_native_preflight.cmd` now validates both native build **and native import**.
- Adds `run_native_diagnostics.cmd` with explicit compiler/DLL path reporting.


## v0.1.2.2

- Performance hotfix; no external constants or target matching added.
- Cache backend loading once per Fourier scan.
- Cache the q-independent shell-0 self Jacobian once per numerical case.
- Full/research campaign keeps the original brute-force interaction Jacobian; regression reproduces v0.1.2.1 outputs exactly on an identical native test grid.
- Added optional C4 Jacobian-column reconstruction for quick/smoke runs, reducing evaluated Jacobian columns by a factor of four when `N % 4 == 0`.
- Added independent rotated-column C4 audit so quick acceleration does not silently disable the symmetry check.
- `run_quick.cmd` now uses `N=32/48`, `dq=0.05`, `max_m=8`.
- Added `run_quick_research.cmd` with `dq=0.025`, `max_m=12`.
- Added C4 acceleration regression and `PERFORMANCE.md`.
- Added exact-config per-case resume so interrupted/repeated campaigns do not recompute completed cases.

## v0.1.2.1

- Windows native-build hotfix only; no numerical/scientific algorithm changes.
- Removed invalid MinGW linker argument `-lpython3.14`; Windows now links only against the CPython import-library name `-lpython314` for Python 3.14.
- Setuptools fallback now checks for `setuptools` before launching the generated setup script and prints the exact requirements-install command when unavailable.
- Added `run_install_requirements.cmd` for explicit one-command environment setup.
- Native C++ source and Fourier/convergence logic are byte-identical to v0.1.2.

## v0.1.2

- Added signed azimuthal Fourier basis `m=-M...M`.
- Added low-mode projected operator and truncation-leakage diagnostic.
- Added explicit C4 sector decomposition appropriate to the cubic periodic image lattice.
- Added C4 symmetry-leakage gate; `m <-> m+4k` mixing is treated as allowed sector physics, not as a symmetry failure.
- Added per-sector branch tracking using phase-invariant eigenvector overlap.
- Added dominant signed-m, dominant-|m| weight, and normalized participation entropy.
- Added Fourier-sector marginal-real-part transitions and branch-local `|lambda|` minima.
- Global spectrum retained only as a reference; it cannot promote v0.1.2 candidates.
- Resolution ladder changed to `N=48,64,96,128`.
- Promotion now requires same candidate kind + same C4 sector + same dominant `|m|` across numerical ladders.
- Added high-resolution `N96/N128` gate and `N64/N96/N128` triplet gate.
- Added synthetic circulant and C4-coupled operator regressions.
- Added small physical Fourier-reference probe.
- Preserved dimensionless blind protocol and zero external-target matching.
- `setuptools` remains explicitly present in `requirements.txt`.

## v0.1.1

- Added convergence ladders, mode overlap tracking, adaptive refinement, and finite-difference roundoff gate.

## v0.1.0

- Initial dimensionless finite-core periodic-ring spectral selector.
