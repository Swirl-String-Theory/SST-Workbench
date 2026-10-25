# Scientific scope — A044 v0.2.0

## Frozen blind question

For the final published GRB 221009A data, which generic subluminal dispersion classes remain observationally admissible before any SST-specific quantity is visible?

The paper parametrizes

$$
p^2 = E^2\left[1+\xi_n\left(\frac{E}{E_{\rm LIV,n}}\right)^n\right],\qquad \xi_n=+1,\quad n\in\{1,2\},
$$

and finds the Carpet event compatible with specific subluminal LIV frameworks under the 95% upper bounds

$$
E_{\rm LIV,1}<1.22^{+0.19}_{-0.22}\times 10^{21}\ {\rm GeV},
$$
$$
E_{\rm LIV,2}<2.03^{+0.17}_{-0.22}\times 10^{13}\ {\rm GeV}.
$$

## Primary source-derived gates

1. **Conventional propagation:** final Letter states an expected Carpet count of order \(10^{-96}\), far below the one-event 5% Poisson threshold.
2. **ALP only:** throughout the stated ALP parameter range the expected count remains \(\lesssim O(10^{-4})\), also below the same threshold.
3. **Transparency bounds:** use the final published 95% upper bounds above.
4. **Polarization:** generic birefringent \(n=1\) models conflict with the quoted polarization lower bound \(E_{\rm LIV,1}>3.6\times10^{34}\,\mathrm{GeV}\); this bound is not applied to explicitly nonbirefringent frameworks.
5. **Legacy A044-v0.1 lower bounds:** preserved as conditional compatibility checks rather than universal hard bounds, because their applicability depends on the photon/electron sector, interaction kinematics and source-timing assumptions.
6. **Published nonlinear timing scale:** the Letter reports the independent Ofengeim--Piran value \(E_{\rm LIV,2}=1.59^{+0.56}_{-0.35}\times10^{12}\,\mathrm{GeV}\) as compatible with its transparency upper bound.

## Derived diagnostics, not source claims

The package additionally derives:

- leading-order group velocity from the stated dispersion law;
- a flat-\(\Lambda\)CDM time-of-flight inversion from the Carpet/LHAASO arrival-time window;
- the leading head-on \(\gamma\gamma\to e^+e^-\) threshold shift;
- a local effective power-law order and scale from arbitrary candidate \(\delta(E)=1-v_g(E)/c\) samples.

These are **model diagnostics**. They do not reproduce the paper's complete optical-depth likelihood, source-spectrum fit, detector response, or Supplemental Material scan.

## Critical assumptions

- the Carpet photonlike event is associated with GRB 221009A;
- standard energy-momentum conservation is used in the threshold diagnostic;
- electrons are treated with standard dispersion in that diagnostic;
- the simple timing inversion assumes the high-energy and lower-energy photons are emitted in the same physical episode; therefore that gate is `CONDITIONAL`, not a hard rejection gate;
- Planck-like flat-\(\Lambda\)CDM parameters are used only for the diagnostic cosmological integral and are configurable.

## SST falsification rule

No SST parameter may be fitted to the GRB constraints. A candidate photon/eigenmode law must be generated independently, frozen, hashed, and only then compared with the blind windows.

If no such candidate exists, the scientifically correct result is:

`OPEN_NO_INDEPENDENT_CANDIDATE`