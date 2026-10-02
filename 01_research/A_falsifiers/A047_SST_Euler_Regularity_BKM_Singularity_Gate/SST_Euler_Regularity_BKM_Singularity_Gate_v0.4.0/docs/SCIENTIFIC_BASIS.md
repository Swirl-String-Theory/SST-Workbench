# Scientific basis — v0.4.0

For smooth incompressible Euler,

\[
\partial_t u+(u\cdot\nabla)u=-\nabla p,\qquad \nabla\cdot u=0,
\]

and

\[
D_t\omega=(\omega\cdot\nabla)u=M\omega,\qquad M=\nabla u.
\]

Writing `M=S+W` gives the local stretching rate along vorticity direction `xi=omega/|omega|`:

\[
D_t |\omega|=\alpha|\omega|,\qquad \alpha=\xi^T S\xi.
\]

The deformation gradient satisfies

\[
\dot F=M F,\qquad \det F=1,
\]

and incompressible Euler gives the Cauchy relation

\[
\omega(X(a,t),t)=F(a,t)\omega_0(a).
\]

Taking a material derivative of `F_t=M F` and using `D_t M+M^2=-H`, `H=grad grad p`, gives

\[
F_{tt}=-H F.
\]

The Beale--Kato--Majda continuation criterion makes

\[
\int_0^T ||\omega(t)||_\infty\,dt
\]

the relevant continuation observable. v0.4.0 does not claim that a finite-window power-law fit proves singularity; it treats such a fit only as an escalation signal after numerical, seed/core, convergence, mechanism and robustness gates.

## Model competition

The finite-time model is

\[
\omega_{\max}(t)=A(t_*-t)^{-\gamma}.
\]

It is compared on the same log-amplitude observations against exponential and nonsingular algebraic growth with AICc. Window stability and resolution stability are required because a single late-window linearization can give a misleading `t_star`.

## References

```latex
\begin{thebibliography}{99}
\bibitem{BealeKatoMajda1984}
J.~T. Beale, T. Kato, and A. Majda,
``Remarks on the breakdown of smooth solutions for the 3-D Euler equations,''
\emph{Commun. Math. Phys.} \textbf{94}, 61--66 (1984).

\bibitem{Constantin2000}
P. Constantin,
``The Euler equations and nonlocal conservative Riccati equations,''
\emph{Int. Math. Res. Not.} 2000, 455--465 (2000).
\end{thebibliography}
```
