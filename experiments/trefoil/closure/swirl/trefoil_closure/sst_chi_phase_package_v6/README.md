# SST chi-phase package v6: smooth-matched root selector

This package supersedes v1/v2 as canon-supporting evidence. v1/v2 are now best
classified as archived shared-moment arithmetic/implementation checks. v3/v4/v5
opened the non-tautological question: which resolved vortex-core profile
actually gives the internal torsional phase speed?

v6 focuses on the strongest v5 candidate family:

\[
f_{a_0}(x)
=
x\left[a_0+(3-2a_0)x^2+(a_0-2)x^4\right],
\qquad x=r/a_{\rm core}.
\]

This family satisfies

\[
f(0)=0,\qquad f(1)=1,\qquad f'(1)=-1,
\]

so it is regular at the axis, matches the boundary speed, and matches the
exterior \(1/r\) slope at the boundary.

For uniform density, the profile-derived torsional speed is

\[
\left(\frac{c_\chi}{v_{\rm ref}}\right)^2
=
4\int_0^1 f_{a_0}(x)^2 x^3\,dx
=
\frac{2a_0^2+13a_0+78}{105}.
\]

Therefore the closure condition \(c_\chi/v_{\rm ref}=1\) is exactly

\[
2a_0^2+13a_0-27=0,
\]

with physical positive root

\[
a_0^\star=\frac{\sqrt{385}-13}{4}\approx1.6553542176.
\]

This is close to the golden ratio \(\varphi\approx1.6180339887\), but it is not
equal to it. At \(a_0=\varphi\), the package reports
\(c_\chi/v_{\rm ref}\approx0.99652018\).

## Files

- `simulate_chi_phase_v6.py` — main runner and plots.
- `sst_chi_phase_v6_py.py` — pure-Python backend.
- `sst_chi_phase_v6.cpp` — optional pybind11 C++ backend.
- `sst_chi_phase_v6_build.py` — Windows-safe local build helper.
- `exports/` — generated CSVs, plots, and summary.

## Run

```powershell
python simulate_chi_phase_v6.py
```

Force pure Python:

```powershell
python simulate_chi_phase_v6.py --python
```

Force C++ rebuild:

```powershell
python sst_chi_phase_v6_build.py --force
```

## Status

v6 confirms an exact root inside one admissible smooth-matched profile family.
It is **not** a proof that SST/Euler/NLSE dynamically selects this profile. The
next required step is a variational core equation or Euler/NLSE selector that
selects \(a_0^\star\) without imposing \(c_\chi/v_{\rm ref}=1\) as a closure condition.
