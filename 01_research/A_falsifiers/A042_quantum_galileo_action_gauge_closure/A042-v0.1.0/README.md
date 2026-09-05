# SST Quantum Galileo Action–Gauge Closure Falsifier v0.1.0

## Scientific question

This package tests whether an SST action-scale closure can remain consistent with the
Quantum Galileo Interferometer (QGI) free-fall phase while keeping the laboratory-frame
action and accelerated-frame gauge description mutually consistent.

The primary experimental target is

\[
\Delta\phi_{\rm QGI}(T)=-\frac{m g^2 T^3}{3\hbar},
\]

with the generalized levitation-arm result

\[
\Delta\phi(a,T)=\frac{m\,a(a-2g)}{3\hbar}T^3.
\]

For finite kick duration \(T_{\rm kick}\) and delay \(T_d\), the paper's analytical
approximation used by this package is

\[
\Delta\phi_{\rm finite}
=
\frac{m g^2}{3\hbar}
\left[
T^3+T^2T_{\rm kick}
+T(T_{\rm kick}^2+T_{\rm kick}T_d)
-T_d(T_{\rm kick}+T_d)^2
\right].
\]

The package independently computes the ideal laboratory-frame classical action for the
ballistic path

\[
z(t)=\frac{g}{2}(T^2-t^2),\qquad -T\le t\le T,
\]

using

\[
L_N=\frac12m\dot z^2-mgz,
\]

and checks that

\[
\frac{S_N}{\hbar}=
-\frac{m g^2T^3}{3\hbar}.
\]

It then checks the accelerated-frame closure through the total-derivative boundary term

\[
F(z_E,t)=-mgtz_E+\frac13mg^2t^3,
\]

for which

\[
L_N=L_E+\frac{dF}{dt}.
\]

## SST action-scale branch

The preregistered SST action quantum used in the SST branch is

\[
h_{\rm SST}
=
4\pi^2\rho_{\text{core}}
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}r_c^4,
\qquad
\hbar_{\rm SST}=\frac{h_{\rm SST}}{2\pi}.
\]

Canonical constants:

- \(\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}=1.09384563\times10^6\ {\rm m\,s^{-1}}\)
- \(r_c=1.40897017\times10^{-15}\ {\rm m}\)
- \(\rho_{\text{core}}=3.8934358266918687\times10^{18}\ {\rm kg\,m^{-3}}\)
- \(\rho_{\!f}=7.0\times10^{-7}\ {\rm kg\,m^{-3}}\)

With these values, the package should recover approximately

\[
h_{\rm SST}=6.62606951568\times10^{-34}\ {\rm J\,s},
\]

which differs from the exact SI Planck constant by about \(-9.57\times10^{-8}\)
fractionally. This is far below the few-percent QGI prefactor sensitivity of the 2026
experiment, so **v0.1.0 cannot claim discrimination of \(h_{\rm SST}\) from \(h\)**.

## What v0.1.0 falsifies — and what it does not

### It does test

1. \(T^3\) phase scaling.
2. QGI prefactor consistency.
3. Numerical classical-action closure.
4. Laboratory-frame / freely-falling-frame gauge closure.
5. Generalized \(a(a-2g)\) law.
6. Finite-pulse zero-duration limit.
7. Blind dataset integrity.
8. Presence and numerical qualification of both relaxed and shader-derived knot sources.
9. Source-family robustness after reveal.

### It does **not** yet test

v0.1.0 does **not** invent a knot-to-QGI coupling. No SST-canonical first-principles
mapping from a microscopic knot geometry to the \(^{87}\mathrm{Rb}\) QGI action was supplied
in the source material. Therefore knot geometry is used as a blinded carrier/provenance
and numerical-robustness axis, not as an ad-hoc correction to the measured phase.

A successful run is therefore reported as

`MACRO_ACTION_GAUGE_CLOSURE_PASS__KNOT_MICRODYNAMICS_UNTESTED`

rather than "SST confirmed".

That distinction is intentional.

---

# Shader-derived knot set

The shader-derived family is a **first-class dataset**.

The package contains an independent geometry implementation of the anisotropic
trefoil-track family

\[
\mathbf X(t)=
\mathbf U[R+a\cos(3t)]\cos(2t)
+\mathbf V[R+a\cos(3t)]\sin(2t)
+\mathbf N[b\sin(3t)+z_0].
\]

The compatibility sweep contains 48 candidates:

- 3 values of `baseR`,
- 4 values of `bulge_R = a`,
- 4 values of `z_weave = b`,
- 512 raw points, resampled uniformly before qualification.

The historical SST Knot Geometry Library example
`baseR=4.08248290463863`, `bulge_R=2.2`, `z_weave=3.0`
is included exactly in this sweep.

If an external shader-derived dataset is available, set:

```bat
set SST_SHADER_DERIVED_ROOT=C:\path\to\shader-derived\set
```

The external set is added as a separate shader-derived provenance arm; the built-in
compatibility sweep remains present so the run is reproducible.

The relaxed dataset defaults to the established SST path:

```text
..\..\KnotPlot\knots\final
```

Override it with:

```bat
set SST_RELAXED_KNOT_ROOT=C:\path\to\KnotPlot\knots\final
```

---

# Blind/reveal rules

The blind stage hides:

- source family,
- source path,
- constructor parameters,
- topology hint,
- real carrier ID.

Public blind artifacts contain only anonymous IDs, immutable geometry hashes, resampling
metadata, and a source-stratum token that does not reveal the source name.

The private reveal file is written to:

```text
.\private\reveal_key.json
```

It is **never** included in the blind ZIP and is also excluded from the shareable revealed
ZIP. The revealed ZIP contains the revealed manifest, not the HMAC secret.

---

# Output convention

Results are written to:

```text
.\SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.0-outputs\
```

Packaging creates:

```text
..\SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.0-outputs_BLIND.zip
..\SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.0-outputs_REVEALED.zip
```

No generic `.\outputs\` directory is used.

---

# One-click Windows run

```bat
run_all.cmd
```

Pipeline:

1. create/update `.venv`;
2. install Python dependencies;
3. build the C++17/pybind11 backend;
4. run regression tests;
5. prepare blind carriers;
6. run BASIC;
7. run EXTENDED;
8. reveal;
9. package BLIND and REVEALED archives.

Blind-only run:

```bat
run_all_blind.cmd
```

Reveal later:

```bat
run_reveal.cmd
```

---

# Important gate semantics

If the relaxed dataset path is absent, the numerical QGI closure can still run, but the
final result is deliberately downgraded to

`DATASET_INCOMPLETE__RELAXED_SOURCE_MISSING`.

A source-complete PASS requires both:

- `shader_derived`
- `relaxed`

after reveal.

---

# References

See `REFERENCES.tex`.
