# SST Research Track — speculative swirl clock A↔B

## Status

**NOT CANON. PASSIVE DIAGNOSTIC. NO SOLVER COUPLING.**

This module does not modify the filament equation, circulation, timestep, topology guard, core radius, or collision dynamics. It only compares two candidate clock routes for two SST carriers.

## Route 1 — mutual-field envelope

For carrier \(K_i\), the diagnostic evaluates the RMS tangential component of the velocity induced only by the other carrier \(K_j\):

\[
u_i=\left[\frac{1}{L_i}\oint_{K_i}
\left(\mathbf u_{j\to i}\cdot\hat{\mathbf t}_i\right)^2\,ds\right]^{1/2}.
\]

The relative orientation between the canonical internal swirl and the external contribution has not been derived. The code therefore uses a formal bracket rather than a single superposition law:

\[
v_i\in\left[\left|\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}-u_i\right|,
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}+u_i\right].
\]

The interval is mapped through the SST clock ansatz

\[
\eta_i^{\rm field}=\frac{d\tau_i}{dt}
=\sqrt{1-\frac{v_i^2}{c^2}}.
\]

Using \(\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}=1.09384563\times10^6\,\mathrm{m\,s^{-1}}\), the isolated baseline is

\[
\eta_0=0.999993343558553,
\qquad
(1-\eta_0)\times10^6=6.656441447\ \mathrm{ppm}.
\]

The addition of a meter-scale filament velocity to the canonical horn velocity is only a dimensional Research-Track bracket. It is not a derived similarity map.

## Route 2 — body-phase proxy

The code measures the instantaneous body-frame angular rate of each full carrier and compares it with a fixed reference:

\[
\eta_i^{\rm phase}=\frac{|\Omega_{{\rm body},i}|}{|\Omega_{{\rm body},i,0}|}.
\]

The reference should be calibrated once at the largest available A–B separation. It must not be recalibrated during the distance sweep.

`Omega_body` is a geometric phase proxy, not yet the internal SST clock phase. Replacing it with a canonically derived internal phase observable is a required future step.

## Two-sided closure

The field route supplies an interval

\[
R_{AB}^{\rm field}
=\frac{\eta_A^{\rm field}}{\eta_B^{\rm field}}
\in [R_{\min},R_{\max}],
\]

while the phase route supplies

\[
R_{AB}^{\rm phase}
=\frac{\eta_A^{\rm phase}}{\eta_B^{\rm phase}}.
\]

The UI reports `VOORLOPIG INGESLOTEN` only when

\[
R_{AB}^{\rm phase}\in[R_{\min},R_{\max}].
\]

This is a finite-time screening result, not a proof.

## Operating protocol

1. Select `botsing`, medium `SST`, two identical knot carriers, and a fixed topology.
2. Start with maximum carrier separation.
3. Activate the red speculative-clock button and accept the warning.
4. Calibrate the phase reference once.
5. Run the approach without recalibration.
6. Record separation, mutual tangential RMS velocity, both field intervals, phase ratio, accumulated differential clock time, and closure residual.
7. Repeat with higher resolution, different `a_sim`, A/B exchange, reversed traversal orientation, and both LIA and Biot–Savart where applicable.

## Gates required before canonization

- **Large-distance limit:** \(R_{AB}\to1\) as \(d_{AB}\to\infty\).
- **Exchange symmetry:** swapping A and B inverts the ratio without changing its magnitude law.
- **Resolution convergence:** results converge under increasing centerline resolution and smaller deterministic timestep.
- **Core independence:** inferred clock ratio does not materially depend on numerical \(a_{\rm sim}\).
- **Frame independence:** no dependence on display frame; solver-frame representations agree when physically equivalent.
- **Phase definition:** replace `Omega_body` with an internal phase variable derived from SST dynamics.
- **Superposition law:** derive how external swirl modifies the internal clock speed; the current plus/minus envelope is only a bound.
- **Backreaction:** determine whether clock modification affects knot dynamics, while avoiding circular fitting.
- **Falsifiability:** establish a distance-, orientation-, and chirality-dependent prediction before fitting to data.

## Interpretation

A red result rejects the selected parameterization or proxy. A green result identifies a candidate regime for stricter derivation and replication; it does not establish physical time dilation.

## Adjustable two-knot start distance

The collision configuration now exposes the initial axial centre separation

\[
\Delta z_{AB,0}=|z_B-z_A|.
\]

Carrier A and B are reset symmetrically around their existing midpoint:

\[
z_A=z_m-\frac{\Delta z_{AB,0}}{2},\qquad
z_B=z_m+\frac{\Delta z_{AB,0}}{2}.
\]

The lateral offset remains independent. Therefore the initial Euclidean centre distance is

\[
d_{AB,0}=\sqrt{\Delta z_{AB,0}^{2}+\Delta x^{2}}.
\]

Changing \(\Delta z_{AB,0}\) rebuilds the knot geometry and deliberately clears the phase calibration. A distance sweep must therefore be run as follows:

1. choose the largest intended \(\Delta z_{AB,0}\);
2. reset and calibrate the phase proxy once;
3. evolve the knots toward each other using the prescribed drift, without recalibration;
4. for a static distance scan, record each run separately and use the same far-distance reference externally;
5. reject settings whose initial centreline clearance is below the topology-guard stop threshold.

The control does not bypass the topology guard. It reports the initial total centre distance, the current centre distance, the measured centreline clearance, and the active stop threshold.
