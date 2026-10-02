# Operator-split arclength remap — v0.3.2

The v0.3.1 long integrator evaluated

\[
\dot{\mathbf X}=\mathbf u_{\rm phys}(\mathbf X)+\mathbf u_{\rm mesh}(\mathbf X)
\]

inside every RK4 stage.  Although \(\mathbf u_{\rm mesh}\) was pointwise tangential, a finite polygon and nonlinear RK4 stage evaluation can feed this relabeling back into the evaluated physical field.

v0.3.2 instead applies

\[
\mathbf X_{n+1}^{-}=\Phi_{\Delta t}^{\rm RK4}[\mathbf X_n],
\qquad
\mathbf X_{n+1}=\mathcal R_s[\mathbf X_{n+1}^{-}]
\]

only when a preregistered physical remap time is reached.  \(\mathcal R_s\) is uniform closed-curve polygonal arclength resampling with fixed point count and preserved first-marker phase anchor.

S37C varies the physical remap interval and asks whether the embedded curve converges as spatial resolution increases.  Existing S37A thresholds are reused for final-shape, score and AUC sensitivity; no looser physics criterion is introduced.
