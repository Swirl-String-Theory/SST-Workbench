# Scientific basis

For smooth 3-D incompressible Euler,

\[
(\partial_t+\mathbf u\cdot\nabla)\boldsymbol\omega=(\boldsymbol\omega\cdot\nabla)\mathbf u.
\]

The Beale--Kato--Majda continuation criterion implies that a smooth solution can continue beyond T if

\[
\int_0^T \|\boldsymbol\omega(t)\|_{L^\infty}\,dt < \infty.
\]

OpenAI (2026) reports smooth compactly supported divergence-free initial data for unforced 3-D Euler whose smooth solution has finite maximal lifespan and divergent BKM integral. Their amplification construction tracks particle deformation F, velocity gradient M, pressure Hessian H, and localized oscillatory packets. v0.1.0 therefore records max-vorticity, local strain and strain-vorticity alignment, while introducing a localized divergence-free high-frequency packet as an adversarial perturbation.

## References

```latex
\begin{thebibliography}{99}
\bibitem{OpenAIEuler2026}
OpenAI, 2026, ``Finite Time Blowup for the Euler Equation,'' preprint.
\url{https://cdn.openai.com/pdf/315b36cd-ec98-4023-8342-93345194ece1/euler.pdf}

\bibitem{BealeKatoMajda1984}
J.~T. Beale, T. Kato, and A. Majda, 1984,
``Remarks on the breakdown of smooth solutions for the 3-D Euler equations,''
\emph{Communications in Mathematical Physics} 94, 61--66.
\doi{10.1007/BF01212349}
\end{thebibliography}
```
