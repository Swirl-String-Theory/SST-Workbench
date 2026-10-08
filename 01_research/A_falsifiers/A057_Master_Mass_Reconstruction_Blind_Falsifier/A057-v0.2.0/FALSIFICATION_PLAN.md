# Falsification plan — A057 v0.2.0

## Primary chain

\[
\text{E013 frozen E011 carrier}
\rightarrow
\widehat H_K
\rightarrow
\text{stationarity}
\rightarrow
L\leftrightarrow H
\rightarrow
\nabla^2H
\rightarrow
J
\rightarrow
\operatorname{spec}J
\rightarrow
\Lambda_K
\rightarrow
\text{target-free frozen predictions}.
\]

The critical methodological change is that **carrier selection is no longer an A057 degree of
freedom**. E013 freezes it first. A057 cannot replace an inconvenient or unavailable carrier.

## Common-carrier binding gate

Before the energy program, A057 requires:
- E013 manifest schema `E013-COMMON-CARRIER-MANIFEST-1`;
- E011 release `E011-v0.3.0`;
- explicit `legacy_falsifier_outputs_used_as_evidence=false`;
- unique static seed IDs;
- source byte reload for every carrier;
- `raw_sha256` agreement when supplied;
- exact `geometry_sha256` agreement.

Failure is retained as G1 evidence. No legacy dataset is searched as fallback.

## Energy kernel

The operational finite-core line Hamiltonian remains

\[
H_a=\frac{\rho\Gamma^2}{8\pi}
\sum_{ij}\oint_{K_i}\!\oint_{K_j}
\frac{d\mathbf X_i\cdot d\mathbf X_j}
{\sqrt{\|\mathbf X_i-\mathbf X_j\|^2+a^2}}.
\]

It is compared with the independent bounded core-tube quadrature as a reduced 3-D diagnostic.

## State authority

A057 does not assume that a `STATIC_READY` geometry is an equilibrium state. For the reduced
Bishop perturbation coordinates,

\[
\sigma_{\rm stat}
=
\frac{\|\nabla U(0)\|}{\max(|U(0)|,\epsilon)}.
\]

Only carriers below the profile-frozen threshold are stability candidates. The Hessian/Jacobian
is still computed for failed carriers under diagnostic-continuation, but those spectra are excluded
from the certified within-topology spectral-ratio gate.

A057-v0.2.0 does **not** introduce an unregistered relaxation algorithm. A future restoring/
self-confinement falsifier must establish such a state-selection mechanism independently on the
same E013 carrier IDs.

## Evidence roles

- E011 `CROSS_PROVIDER_ROBUST`: strongest static carrier evidence.
- E011 `CROSS_PROVIDER_SENSITIVE`: valid carrier, explicit provider uncertainty.
- E011 `SINGLE_PROVIDER_QUALIFIED`: carrier diagnostics only; cannot close replication.
- E013 unavailable topology: no substitute geometry.

## Blind/reveal

All observed mass targets and protected historical numerical targets remain private through
FULL/CERTIFY. `PREDICTIONS_FROZEN.json` must exist before reveal. Historical formulas remain
post-reveal competitors, never discovery targets.
