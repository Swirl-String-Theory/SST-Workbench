# SST Finite-Core Axial–Toroidal Eigenmode + Self-Generated Phase-Delay Blind Falsifier v0.1.1

A turnkey Windows/Python/C++ package testing whether a **finite vortex core** can carry a mixed axial/toroidal eigenmode whose **self-generated loop phase** predicts spectral stabilization.

The non-negotiable constraint remains

\[
\boxed{\text{no feedback delay is supplied to the dynamics.}}
\]

The code measures the delay from the finite-core dispersion relation and an independent wave-packet return.

## v0.1.1 integrity upgrade

This release fixes the main issues exposed by the v0.1.0 output audit:

1. carrier closure votes use **only pairs for which CLOSED and control modes both pass the eigenmode gate**;
2. delay statistics use **only valid CLOSED modes with a valid return measurement**;
3. neutral/neutral growth is an explicit `TIE`, so numerical \(10^{-12}\)-scale values cannot create huge ratios;
4. the old one-sided offset control is replaced by the symmetric control
   \[
   g_{\rm ctrl}=\frac{g(k_0-\Delta k)+g(k_0+\Delta k)}{2},
   \]
   which cancels the first-order dispersive slope about exact loop closure;
5. the exploratory v0.1.0 \(m=1\) phase signal is converted into a **new-carrier confirmatory campaign**;
6. \(m=2\) is run separately as a negative/control branch;
7. Swirl-Clock observables are emitted explicitly in every CLOSED case and in `SWIRL_CLOCK.csv`.

## Swirl-Clock variables

For the eigenmode convention

\[
\delta q\propto e^{\lambda t},\qquad \lambda=\sigma+i\omega_\lambda,
\]

v0.1.1 reports

\[
\boxed{
\{\Re\lambda,\Im\lambda,T_{\rm mode},v_g,\tau_{\rm loop},\tau_{\rm return},\phi_{\rm loop},\Omega_{\rm swirl}\}.
}
\]

with

\[
T_{\rm mode}=\frac{2\pi}{|\Im\lambda|},\qquad
\tau_{\rm loop}=\frac{L}{|v_g|},\qquad
\phi_{\rm loop}=\phi_{\rm measured}(\tau_{\rm return}).
\]

`omega_mode = abs(Im(lambda))` is also written explicitly because the internal solver uses the equivalent sign convention `omega = -Im(lambda)`.

See `docs/SWIRL_CLOCK.md` for the exact field definitions.

## Symmetric closure falsifier

Exact closed-loop quantization is

\[
k_0L+m\Theta_B=2\pi n.
\]

The control uses the same carrier, finite-core profile, axial flow, core radius and \((m,n)\), but evaluates both

\[
k_-=k_0-\Delta k,\qquad k_+=k_0+\Delta k.
\]

The control growth is their mean. Therefore a linear local trend \(dg/dk\) cannot by itself make the exact-closure point win.

## New preregistered phase confirmation

The v0.1.0 extended campaign discovered, post hoc, an \(m=1\) candidate phase near

\[
\phi_\star\approx2.72\ \mathrm{rad}\approx156^\circ.
\]

v0.1.1 freezes that value **before running new carriers**. It is used only in reveal/scoring, never in the dynamics or eigenproblem.

The confirmatory carriers are:

- analytic \(T(2,5)\), \(T(2,7)\);
- analytic \(T(3,4)\), \(T(3,5)\);
- Fremlin `4_1` and `7_2`.

For each carrier the fitted slope of

\[
y=\log\!\frac{g_{\rm CLOSED}+\epsilon}{g_{\rm sym}+\epsilon}
\]

against

\[
x=\cos(\phi_{\rm loop}-\phi_\star)
\]

must be negative. A carrier-level exact sign test then determines whether the directional prediction replicates.

## One-click runs

Basic installation/native build/tests/basic campaign:

```cmd
run_all.cmd
```

The most important new test is:

```cmd
run_all_swirl_clock_m1_confirmatory.cmd
```

and its branch-specificity control:

```cmd
run_all_swirl_clock_m2_control.cmd
```

Existing broad scans remain available:

```cmd
run_all_extended.cmd
run_all_profile_robustness.cmd
run_all_core_radius.cmd
run_all_chirality_sign.cmd
run_all_radial_convergence.cmd
```

Everything:

```cmd
run_all_full.cmd
```

`OMP_NUM_THREADS=16`; BLAS is deliberately pinned to one thread for the small generalized eigenproblems.

## Interpretation

For an ideal inviscid mode the strongest target is not artificial damping but

\[
\Re\lambda\rightarrow0,\qquad |\Im\lambda|>0.
\]

The package therefore keeps **clock rate** and **stability** separate:

\[
\underbrace{|\Im\lambda|}_{\text{mode tick rate}}
\quad+\quad
\underbrace{\tau_{\rm return}}_{\text{return time}}
\quad\longrightarrow\quad
\underbrace{\phi_{\rm loop}}_{\text{measured feedback phase}}
\quad\stackrel{?}{\longrightarrow}\quad
\underbrace{\Re\lambda}_{\text{growth response}}.
\]

A positive v0.1.1 result is still only a gate toward a full curved finite-core Euler/Floquet or nonlinear calculation; it is not by itself proof of an SST particle.
