# SST chi-phase verification package v2

Self-contained Research Track verification package for the internal torsional phase sector
\(\chi(s,t)\) in Swirl-String Theory (SST).

This package follows the same local build/run style as the `sst_macro_wake` package:

```powershell
python sst_chi_phase_v2_build.py --force
python simulate_chi_phase_v2.py
```

If the C++/pybind11 extension cannot be built, the runner automatically falls back to
`sst_chi_phase_v2_py.py`.

## What v2 tests

The local chi-sector ansatz is:

\[
\mathcal I_\chi = \rho_f \int_A r_\perp^2\,dA,
\qquad
\mathcal K_\chi = \rho_f v_{\rm swirl}^2 \int_A r_\perp^2\,dA.
\]

Therefore

\[
c_\chi^2=\frac{\mathcal K_\chi}{\mathcal I_\chi}=v_{\rm swirl}^2.
\]

v2 strengthens v1 by testing more than circular cross-sections:

1. **Circle radius sweep** over several \(a_{\rm core}/r_c\).
2. **Annular cross-sections**, testing hollow resolved tubes.
3. **Elliptical/anisotropic cross-sections**, testing whether the shared-moment ansatz avoids spurious speed splitting.
4. **Counterfactual anisotropic split diagnostic**, showing what failure would look like if inertia and stiffness did not share the same transverse moment tensor.
5. **Horn-loop phase spectrum**, testing

\[
L_\chi=2\pi r_c
\quad\Rightarrow\quad
\omega_n\approx n\omega_c.
\]

6. **Finite-difference spectrum convergence**, proving that the small high-mode error is numerical dispersion, not physics.

## Files

- `simulate_chi_phase_v2.py` — main runner; creates CSV/PNG exports.
- `sst_chi_phase_v2.cpp` — optional pybind11 C++ kernel.
- `sst_chi_phase_v2_build.py` — Windows-safe build helper.
- `sst_chi_phase_v2_py.py` — pure-Python fallback.
- `exports/` — generated after running the simulation.

## Status

This is a **Research Track sanity verifier**. Passing it supports the local mechanical
claim

\[
\chi\rightarrow U(1)_\chi,
\qquad
c_\chi=v_{\rm swirl},
\]

under the shared transverse-moment assumption. It does **not** prove:

- \(Q_\chi\to Q_{\rm em}\),
- electrodynamics,
- \(SU(2)\),
- \(SU(3)\),
- particle masses.

Those require separate R-phase coupling and non-abelian generator tests.

## Windows notes

The build helper uses a relative C++ source path and a short build-temp folder:

```python
Extension("sst_chi_phase_v2", ["sst_chi_phase_v2.cpp"], ...)
script_args=["build_ext", "--inplace", "--build-temp", "_build_tmp"]
```

This avoids the MSVC object-path issue seen with absolute source paths.

## Run commands

```powershell
cd path\to\sst_chi_phase_package_v2
python simulate_chi_phase_v2.py
```

Force Python fallback:

```powershell
python simulate_chi_phase_v2.py --python
```

Force C++ rebuild:

```powershell
python sst_chi_phase_v2_build.py --force
```

Clean Windows build leftovers:

```powershell
rmdir /s /q _build_tmp
rmdir /s /q build
del sst_chi_phase_v2*.pyd
python sst_chi_phase_v2_build.py --force
```

## Expected interpretation

A successful run should show:

\[
\max |c_\chi/v_{\rm swirl}-1| \approx 0,
\]

for all tested shapes, while the finite-difference spectrum error decreases with grid refinement.

The canonical anisotropic ellipse test should remain unsplit:

\[
c_{\chi,x}/v_{\rm swirl}=c_{\chi,y}/v_{\rm swirl}=1.
\]

The counterfactual curves are intentionally non-canonical and demonstrate the falsifier:
if stiffness and inertia do not share the same moment tensor, anisotropy produces a speed split.
