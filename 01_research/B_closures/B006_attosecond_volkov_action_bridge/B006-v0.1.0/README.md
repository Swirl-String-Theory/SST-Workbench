# SST Attosecond Volkov–Action Bridge v0.1.0

Purpose: define a **measurement bridge**, not a new photoionization theory. The orthodox strong-field/Volkov calculation supplies a complex time-domain kernel. SST is allowed to contribute only a separately derived action difference.

The bridge is

\[
\delta\phi_{\rm SST}=\frac{\delta S_{\rm SST}}{\hbar},
\]

or, in the target-blind mass-specific form used by A042,

\[
\boxed{\delta\phi_{\rm SST}
=\frac{\delta s_{\rm SST}}{(\hbar/m)_{\rm QGI}}},
\qquad
[\delta s]=[(\hbar/m)]=\mathrm{m^2\,s^{-1}}.
\]

No CODATA Planck target is needed in the second form.

For an orthodox kernel \(K_0(t;\mathbf p,\tau)\),

\[
M_0=\int K_0(t)\,dt,
\qquad
M_{\rm SST}=\int K_0(t)e^{i\delta\phi_{\rm SST}(t)}\,dt.
\]

For \(|\delta\phi|\ll 1\),

\[
\delta M=i\int K_0(t)\delta\phi(t)\,dt+O(\delta\phi^2),
\]

and

\[
\boxed{\delta I
=2\operatorname{Re}\!\left(M_0^*\delta M\right)
+O(\delta\phi^2)}.
\]

## Hard null: global phase

If \(\delta\phi(t)=\phi_0\) is constant over the integration coordinate,

\[
M_{\rm SST}=e^{i\phi_0}M_0,
\qquad
|M_{\rm SST}|^2=|M_0|^2.
\]

Therefore a scalar “extra phase” is not enough. The candidate must create a **relative phase structure** inside a coherent amplitude or between explicitly coherent channels.

## Gauge statement

This bridge does **not** claim to prove gauge invariance of the strong-field approximation. A gauge-consistent orthodox kernel remains a prerequisite. The package enforces the weaker but mandatory observable null under a factorable global/boundary phase.

## Directional observable

When opposite momentum hemispheres are available, score the residual only after subtracting the orthodox asymmetry:

\[
A_{\pm}=\frac{I_+-I_-}{I_++I_-},
\qquad
\Delta A_{\pm}=A_{\pm}^{\rm data}-A_{\pm}^{\rm orthodox}.
\]

This prevents ordinary streaking asymmetry from being relabeled as SST.

## Status classes

- **ORTHODOX:** Volkov/SFA kernel, attosecond streaking, angle-resolved intensity.
- **DERIVED BRIDGE:** action-to-phase algebra and first-order intensity response.
- **SST CANDIDATE:** the functional \(\delta s_{\rm SST}[\mathbf v,\boldsymbol\omega,\ldots]\). This package does not invent it.

See `DERIVATION.tex` and `SOURCE_PROVENANCE.md`.
