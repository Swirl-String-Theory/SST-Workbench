# Theory note — v0.2.1

Scientific equations are unchanged from v0.2.0.

The dimensionless centerline dynamics are

\[
\dot{\mathbf X}_i=\mathbf V_{\rm fc}(\mathbf X_i;a)+\epsilon\,\mathsf A(t)\bigl(\mathbf X_i-\bar{\mathbf X}\bigr),
\]

with the regularized segment surrogate

\[
\mathbf V_{\rm fc}(\mathbf X_i;a)=\frac{\kappa_{\rm BS}}{4\pi}\sum_j
\frac{\Delta\boldsymbol\ell_j\times(\mathbf X_i-\mathbf X_{j+1/2})}
{\left(\lVert\mathbf X_i-\mathbf X_{j+1/2}\rVert^2+a^2\right)^{3/2}}.
\]

Here \(\kappa_{\rm BS}\) is an opaque dimensionless numerical coefficient, and the regularization is specified only by \(a/\Delta s\). No SST calibration map is applied.

The two-colour waveform is

\[
\mathbf e(t)=a_1\begin{pmatrix}\cos\omega t\\ \sin\omega t\\0\end{pmatrix}
+a_2\begin{pmatrix}\cos(2\omega t+\phi)\\ s_2\sin(2\omega t+\phi)\\0\end{pmatrix},
\]

where \(s_2=+1\) for COR and \(s_2=-1\) for CNR. The trace-free coupling is

\[
\mathsf A(t)=\mathbf e(t)\mathbf e(t)^\mathsf T-
\frac{\lVert\mathbf e_\perp(t)\rVert^2}{2}\operatorname{diag}(1,1,0).
\]

For CNR the waveform obeys a threefold time-translation/rotation symmetry, and the strain map preserves that covariance. The numerical experiment asks whether the discretized finite-core flow respects the same equivariance within refinement error.
