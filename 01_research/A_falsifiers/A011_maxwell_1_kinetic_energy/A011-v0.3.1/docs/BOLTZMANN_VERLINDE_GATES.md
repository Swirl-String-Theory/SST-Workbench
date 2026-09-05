# Boltzmann–Verlinde–SST gates — v0.3.1

## 1. State-counting discipline

The implementation follows the useful three-level distinction emphasized in the Sharp–Matschinsky translation/commentary of Boltzmann's 1877 paper:

1. microscopic labelled configuration / **complexion**;
2. occupation or state distribution;
3. macroscopic thermodynamic state.

For occupation numbers `w_i` and declared degeneracies `g_i`, the workbench computes

\[
\ln P
=
\ln N! - \sum_i \ln w_i! + \sum_i w_i\ln g_i,
\qquad N=\sum_iw_i .
\]

The calculation uses `lgamma` and therefore never explicitly forms factorials.

When multiple candidate distributions share one `macrostate_id`, the workbench verifies that they have the same `N` and total energy and checks whether the preregistered `observed=true` distribution maximizes `ln P`.

**Guard:** the workbench never creates accessible-state counts from centerline geometry.  Counts must come from a frozen solver/sampler and must be conditioned on the preregistered invariant sector (for example topology, circulation, helicity or other conserved quantities appropriate to the chosen SST dynamics).

## 2. Boltzmann equilibrium gate

For measured occupations `n_i` at energies `E_i`,

\[
p_i \propto g_i e^{-E_i/(k_BT)}.
\]

The package fits

\[
\ln\frac{n_i}{g_i} = a - \beta E_i
\]

and reports `T_fit`, `R^2`, and the KL divergence of the observed normalized occupations from the distribution at the preregistered `temperature_K`.

A failure is promoted to `BOLTZMANN_EQUILIBRIUM` only when

```json
"research_claims": {"boltzmann_equilibrium": true}
```

was frozen before held-out inspection.

## 3. Microcanonical temperature

From sampled accessible-state multiplicity,

\[
S(E,x)=k_B\ln \mathcal N(E,x),
\qquad
\frac{1}{T}=\left(\frac{\partial S}{\partial E}\right)_{x,I_j}.
\]

`state_counts.csv` can therefore provide an independent microcanonical temperature diagnostic.  At least three energy values at fixed position are required.

## 4. Entropy-force gate against SST pressure dynamics

At fixed energy/invariant sector,

\[
F_{\rm ent}(x)
=
T_{\rm eff}(x)
\left(\frac{\partial S}{\partial x}\right)_{E,I_j}
=
k_BT_{\rm eff}(x)
\frac{\partial \ln\mathcal N}{\partial x}.
\]

This is compared with an independent physical reference.  If `hyd_force_N` is absent but the probe mass and pressure gradient are supplied, the SST Euler anchor is evaluated as

\[
F_{\rm hyd}
=-\frac{m}{\rho_{\!f}}\frac{\partial p}{\partial x}.
\]

A sign mismatch is an automatic failure.  Magnitude uses a symmetric relative error to avoid privileging either estimator.

**Blindness requirement:** the sampler that produces `state_counts.csv` may not be tuned using `force_reference.csv`.

## 5. Integrability gate

If the same conservative force is to be represented simultaneously by

\[
T\nabla S = -\frac{m}{\rho_{\!f}}\nabla p,
\]

then a scalar `S` requires

\[
\nabla\!\left(\frac1T\right)\times\nabla p=0.
\]

For nonzero gradients this is equivalent to `grad(T)` being parallel or antiparallel to `grad(p)`.  The workbench tests the sine of the angle between those gradients.  Constant `T` satisfies the integrability condition identically.

## 6. Verlinde entropy-displacement postulate

The optional audit compares the supplied entropy gradient with

\[
\frac{dS}{dx}
=2\pi k_B\frac{mc}{\hbar}.
\]

This is a **conditional comparison**, not an SST identity.

## 7. Holographic-screen tests

For each screen series the package can test:

\[
N\propto A,
\qquad
N=\frac{Ac^3}{G\hbar},
\qquad
E=\frac12Nk_BT.
\]

It reports the fitted slope `d log N/d log A`, inferred `G`, and equipartition ratio.

The canonical hierarchy check is always printed but is not a physical failure:

\[
\left(\frac{r_c}{\ell_P}\right)^2\approx 7.60\times10^{39}.
\]

Consequently a literal identification of one information bit with one SST core area is not silently accepted.

## 8. Inverse-square and potential/entropy tests

Optional radial data are fitted to

\[
|F|\propto r^q,
\qquad q\stackrel{?}{=}-2.
\]

The optional potential relation follows Verlinde's Eq. (3.16):

\[
\frac{\Delta S}{n}
=-\frac{k_B\Delta\Phi}{2c^2}.
\]

These gates are activated independently in `research_claims`.

## 9. What a failure means

- `FALSIFIER_TRIGGERED`: an existing physical Maxwell/SST falsifier was triggered.
- `RESEARCH_CLOSURE_FAILURE`: a preregistered Boltzmann/Verlinde bridge claim failed.
- `NUMERICAL_OR_CLOSURE_FAILURE`: numerical convergence, energy conservation, or taxonomy failed.
- `NO_FALSIFIER_TRIGGERED_NOT_VALIDATION`: nothing implemented failed; this is not confirmation.

## Sources

```latex
\bibitem{Boltzmann1877SharpMatschinsky2015}
L.~Boltzmann, translated and commented by K.~Sharp and F.~Matschinsky,
``On the Relationship between the Second Fundamental Theorem of the Mechanical Theory of Heat and Probability Calculations Regarding the Conditions for Thermal Equilibrium'',
\emph{Entropy} \textbf{17} (2015) 1971--2009; original work 1877,
\href{https://doi.org/10.3390/e17041971}{doi:10.3390/e17041971}.

\bibitem{Verlinde2011OriginGravity}
E.~P.~Verlinde,
``On the Origin of Gravity and the Laws of Newton'',
\emph{Journal of High Energy Physics} \textbf{2011}, 29 (2011),
\href{https://doi.org/10.1007/JHEP04(2011)029}{doi:10.1007/JHEP04(2011)029},
\href{https://arxiv.org/abs/1001.0785}{arXiv:1001.0785}.
```
