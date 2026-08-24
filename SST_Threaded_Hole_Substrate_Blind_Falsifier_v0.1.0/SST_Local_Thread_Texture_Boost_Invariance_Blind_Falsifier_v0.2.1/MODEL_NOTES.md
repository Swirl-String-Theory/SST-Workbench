# Model notes — v0.2.1 explicit local vortex-thread substrate

## 1. Physical distinction being tested

The hypothesis under test is

\[
\boxed{
\text{objective local vortex texture}
\;\not\Rightarrow\;
\text{globally detectable absolute translational velocity}
}
\]

A common velocity offset of the complete local system is therefore treated as a covariance transformation, whereas gradients/orientation/density of explicit vortex threads are local physical structure.

## 2. Why the Earth-like bundle is locally parallel

Let a source radius/observation distance be \(R_s\) and a knot scale be \(\ell_k\).  For Earth- or Sun-scale sources and microscopic particle structures,

\[
\frac{\ell_k}{R_s}\ll1.
\]

Across the knot, a radial source direction changes only by

\[
\Delta\theta=O\!\left(\frac{\ell_k}{R_s}\right).
\]

The v0.2.1 local bundle therefore uses approximately parallel outgoing legs.  This is more appropriate than placing a source center at \(R_s\sim 10R_g\), which would create artificial curvature across the knot.

## 3. Vorticity-line topology

For ordinary smooth incompressible flow,

\[
\boldsymbol\omega=\nabla\times\mathbf v,
\qquad
\nabla\cdot\boldsymbol\omega=0.
\]

A line-vorticity model must therefore not contain free filament endpoints in the fluid domain.  Every v0.2.1 thread is a closed polygonal component.  The remote return path is explicit and its distance is varied to test locality.

## 4. Source anchoring assumption

The thread substrate is frozen relative to the local source frame during a campaign.  The knot evolves dynamically through it, but the source-generated background threads are not mutually deformed by the knot.

This is an assumption, not a derivation.  A later version can add fully coupled thread-thread evolution as a stronger test.  v0.2.1 isolates the question:

\[
\text{Does a committed closed, source-anchored vortex texture have the required covariance/locality behavior?}
\]

## 5. Common boost

For common boost \(\mathbf U_0\),

\[
\mathbf X(t)\rightarrow\mathbf X(t)+\mathbf U_0t,
\qquad
\mathbf T_a(t)\rightarrow\mathbf T_a(t)+\mathbf U_0t.
\]

All Biot--Savart separations are unchanged.  Therefore an intrinsic shape observable should satisfy

\[
\Delta\mathcal O_{\rm intrinsic}=0
\]

up to numerical precision.  G1 is primarily an implementation/covariance gate; it is not independent evidence for relativity.

## 6. Density gradient

A local density-gradient test is generated without thread endpoints by varying the circulation per closed component.  This is equivalent to changing coarse-grained vorticity flux density while preserving closed-line topology.

The chosen gradient law is a committed experimental control.  It is not yet an SST Canon-derived constitutive law.

## 7. Primary + secondary bundle

The second bundle probes a nonparallel local texture.  The labels “Earth-like” and “Sun-like” mean only:

- primary locally generated direction;
- second, nonparallel locally generated direction.

No actual Earth/Sun thread density, circulation, or astronomical falloff is assumed.

## 8. Fixed-core convergence

For each source geometry, \(R_{g,\rm ref}\) is computed with the same fixed reference resampling count at every ladder level.  Therefore

\[
a_{\rm knot}=\alpha_kR_{g,\rm ref},
\qquad
a_{\rm thread}=\alpha_tR_{g,\rm ref}
\]

remain fixed as \(N\) changes.

This separates discretization convergence from changes to the regularized physical model.

## 9. Falsification interpretation

A structural failure has direct meaning for the implemented local-thread architecture:

- G1 fail: common boost leaks into intrinsic shape;
- G2/G3 fail: rigid covariance is broken numerically;
- G4 fail: thread construction/solenoidal consistency is defective;
- G5 fail: local response is contaminated by arbitrary remote closure.

A bridge failure means that the selected closed-thread model does not produce the precommitted dynamical response at the chosen amplitude/resolution.  It does not falsify every possible SST thread constitutive law, but it does falsify this committed realization.

## 10. Minimal next experiments after v0.2.1

If G0--G10 are numerically stable on the relaxed-knot set, the next physically stronger variants are:

1. fully co-evolve source threads and particle knot rather than freezing the background;
2. derive thread circulation/density from SST Canon rather than choosing dimensionless ratios;
3. impose realistic large-source asymptotics and compare Earth-only, Sun-only, and combined local gradients;
4. test observable tensor responses rather than only Kabsch shape distance;
5. test time/phase-clock observables under the same committed thread texture.
