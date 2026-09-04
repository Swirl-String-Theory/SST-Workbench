# SST Quantum Galileo Action–Gauge Closure Falsifier v0.2.0

## New in v0.2.0

v0.2.0 adds the **provenance-clean Geometry/Fluid → Action Quantum gate**.

The primary comparison is intentionally performed in **specific-action units**

\[
[\text{specific action}]
=
\frac{\mathrm{J\,s}}{\mathrm{kg}}
=
\mathrm{m^2\,s^{-1}},
\]

rather than directly predicting an SI value in J·s.

This eliminates the particle mass and the SI kilogram from the primary blind comparison.

---

# 1. QGI side: phase → specific action

Write the fitted experimental phase as a cubic polynomial in the published horizontal variable

\[
t=2T,
\qquad
\phi(t)=c_0+c_1t+c_2t^2+c_3t^3.
\]

For the QGI cubic term,

\[
|c_3|
=
\frac{m g_{\rm eff}^{\,2}}{24\hbar}.
\]

Therefore the experiment determines

\[
\boxed{
\frac{\hbar}{m}
=
\frac{g_{\rm eff}^{\,2}}{24|c_3|}
}
\]

and

\[
\boxed{
\frac{h}{m}
=
\frac{\pi g_{\rm eff}^{\,2}}{12|c_3|}
}
\]

without providing the analysis with \(m\), \(h\), or \(\hbar\).

The primary QGI observable is thus a measured specific action in \(\mathrm{m^2\,s^{-1}}\).

## Raw-data route — preferred

Place a machine-readable population-vs-time file at:

```text
data/qgi/raw/fig2_population_raw.csv
```

The pipeline then reconstructs the phase from the population data using the published analysis structure:

1. upper/lower envelopes;
2. seventh-order envelope polynomials;
3. local mean and visibility;
4. Hilbert-transform phase initialization;
5. phase unwrapping;
6. cubic phase fit;
7. exclusion of the first and last oscillation;
8. direct final fit to the population.

The output is written to:

```text
SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.2.0-outputs/
└─ blind/
   └─ qgi_phase/
      ├─ phase_reconstruction.json
      ├─ phase_reconstructed_from_population.csv
      └─ qgi_specific_action.json
```

## Public-paper fallback

No author-level machine-readable raw population table was identified in the published paper or
its supplementary text. This release therefore **does not fabricate raw data**.

A fallback is supplied:

```bat
run_fetch_qgi_public_pdf.cmd
run_prepare_qgi_phase.cmd
```

It downloads the public arXiv manuscript and first digitizes the **blue population markers in Fig. 2A**. The pipeline then recomputes the phase using the same envelope/Hilbert/cubic/direct-fit stages. That branch is labeled `PUBLISHED_FIGURE2_POPULATION_DIGITIZED`. If Fig. 2 digitization cannot be qualified, a secondary fallback digitizes the red experimental-data fit in Fig. 3A. Both branches are `CONDITIONAL`, never raw-data PASS.

For a one-click public-data run:

```bat
run_all_with_public_qgi.cmd
```

---

# 2. Fluid side: circulation → specific action

The preregistered first model is a uniform Rankine solid-body vortex core.

For a tube with total mass \(M\), core radius \(a\), length \(L\), and total circulation \(\Gamma\),

\[
M=\rho\pi a^2L.
\]

For solid-body rotation,

\[
\Gamma(r)=\Gamma\frac{r^2}{a^2}.
\]

The cross-section averaged intrinsic angular momentum gives

\[
\boxed{
\frac{\hbar_{\rm GF}}{M}
=
\frac{\Gamma}{4\pi}
}
\]

and hence one full phase cycle gives

\[
\boxed{
\frac{h_{\rm GF}}{M}
=
\frac{\Gamma}{2}.
}
\]

The primary blind gate is therefore

\[
\boxed{
\frac{\Gamma_{\rm fluid}}{2}
\stackrel{?}{=}
\left(\frac{h}{m}\right)_{\rm QGI}.
}
\]

This comparison requires neither:

- Planck's constant;
- reduced Planck's constant;
- particle mass;
- electron mass;
- a Compton radius;
- SI kilograms.

## Raw fluid input

Preferred input:

```text
data/fluid/raw/circulation_loop.csv
```

with columns:

```csv
x_m,y_m,z_m,vx_m_s,vy_m_s,vz_m_s
```

The pipeline computes directly

\[
\Gamma
=
\oint\mathbf v\cdot d\boldsymbol\ell.
\]

A matching

```text
data/fluid/raw/circulation_provenance.json
```

must certify that the field/measurement was not constructed using \(h\), \(\hbar\), the
Compton radius, electron mass, or \(\alpha\).

The current canonical SST \(\Gamma_0=2\pi r_c v_{\circlearrowleft}\) is deliberately **not**
used in the primary gate because the current \(r_c\) calibration chain contains \(\hbar\)
upstream.

---

# 3. Where geometry enters — and an important null result

For each blind knot carrier the package measures

\[
L,\quad
\kappa_{\max},\quad
d_{\rm nonlocal},
\]

and defines the explicit numerical tube-radius proxy

\[
a_{\rm proxy}
=
\min\left(
\frac{1}{\kappa_{\max}},
\frac{d_{\rm nonlocal}}{2}
\right).
\]

Then

\[
\widehat L=\frac{L}{a_{\rm proxy}}
\]

is sealed blind.

For the uniform Rankine model,

\[
h_{\rm GF}
=
\frac{\pi}{2}
\widehat L\,
\rho\,\Gamma\,a^3,
\]

while

\[
\frac{h_{\rm GF}}{M}=\frac{\Gamma}{2}.
\]

Thus:

\[
\boxed{
\text{geometry cancels from the leading specific-action prediction.}
}
\]

This is not hidden or patched away. It is reported as a **geometry-null result**.

Geometry remains relevant to:

- absolute tube action;
- tube mass;
- finite-core corrections;
- curvature/profile corrections;
- twist/framing sectors;
- nonuniform velocity profiles.

Those corrections may be added only after they are independently derived and preregistered.

The shader-derived trefoil set remains a first-class blind source alongside the relaxed set.

---

# 4. Why the absolute J·s branch is secondary

An optional branch computes

\[
h_{\rm GF}
=
\frac{\pi}{2}\widehat L\rho\Gamma a^3.
\]

It requires independently measured \(\rho\), \(\Gamma\), and \(a\).

However, an absolute SI result in J·s contains kilograms. Since the SI kilogram is defined
through the fixed numerical value of Planck's constant after the 2019 SI redefinition, this branch
may be **model-provenance-clean** but is not literally metrology-independent of \(h\).

For that reason the primary v0.2.0 gate is the dimensionally equivalent specific-action comparison
in \(\mathrm{m^2\,s^{-1}}\).

---

# 5. Primary gates

The new gates are:

- `G8_QGI_SPECIFIC_ACTION_DATA`
- `G9_FLUID_CIRCULATION_PROVENANCE`
- `G10_SPECIFIC_ACTION_CIRCULATION_CLOSURE`
- `G11_RANKINE_TWO_PI_IDENTITY`
- `G12_GEOMETRY_ACTION_COEFFICIENT_SEAL`

The EXTENDED closure threshold is preregistered at 3%:

\[
\epsilon_{\rm GF/QGI}
=
\left|
\frac{(\Gamma/2)_{\rm fluid}}
{(h/m)_{\rm QGI}}
-1
\right|
\le 0.03.
\]

This is deliberately of the same order as the present experimental QGI sensitivity, rather than
being tuned after seeing a fluid result.

---

# 6. Blind/reveal sequence

Normal strict-blind run:

```bat
run_all.cmd
```

The QGI stage uses this priority:

1. local author/raw `fig2_population_raw.csv`;
2. already-downloaded public arXiv PDF;
3. fixed-source public PDF download followed by Fig. 2 population digitization.

Set

```bat
set SST_QGI_NO_FETCH=1
```

before `run_all.cmd` to disable network acquisition. If the fixed-source download fails, the run continues
with QGI status `NOT_RUN` rather than substituting synthetic data.

`run_all_with_public_qgi.cmd` is retained as an explicit fetch-first wrapper.

The blind run does **not** reveal the Planck target.

Only after the BLIND archive has been sealed:

1. extract the separate `REVEAL_KEY.zip` into the project;
2. run:

```bat
run_reveal.cmd
```

The exact Planck target is used only for secondary reveal diagnostics.

---

# 7. Windows native build compatibility

The package includes all fixes established in v0.1.1:

- explicit setuptools package discovery;
- MSVC-safe `py::ssize_t`;
- Visual Studio 2022 Community/BuildTools support;
- Visual Studio 2026 Community/BuildTools support;
- `x64` and `x86_amd64` fallbacks;
- `DISTUTILS_USE_SDK=1` and `MSSdk=1` after a valid `cl.exe` is found.

---

# Scientific status

A `G10 PASS` would mean:

> the preregistered Rankine-core fluid circulation predicts the same specific action scale as
> independently extracted from QGI phase data, within the preregistered tolerance.

It would **not** establish all of SST.

A `G10 FAIL` would falsify this declared Geometry/Fluid → Action Quantum closure at the tested
precision.

If no provenance-clean raw fluid circulation is supplied, the correct status is `NOT_RUN`, never
an automatic PASS.
