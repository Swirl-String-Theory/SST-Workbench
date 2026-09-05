# Theorem Target v0.0.4 — Boundary Microstates, Area Density, and Relative Entropy

## Status

\[
\boxed{
\text{CLOSED-CONDITIONAL / MICROSTATE THEOREM}
}
\]

with the separate phenomenological verdict

\[
\boxed{
\text{INDEPENDENT CORE-SCALE PIERCINGS FAIL THE OBSERVED GR COEFFICIENT.}
}
\]

The theorem derives \(\eta_A^{\mathrm{SST}}\) and
\(\delta S_{\mathrm{boundary}}=S_{\mathrm{rel}}\) from an explicit boundary
microstate ensemble. It does **not** establish that the full nonlinear SST
substrate realizes that ensemble. It also demonstrates that the simplest
independent \(r_c\)-scale piercing model cannot reproduce the observed
long-range gravitational coupling.

## 1. Source-supported starting point

The current SST Research Track proposes Route I through

\[
S=\eta_A A,
\qquad
T_{\mathrm{SST}}=\frac{\hbar a}{2\pi c k_B},
\qquad
\delta Q=T\,dS,
\]

and explicitly states that a line-piercing entropy model is admissible while
its coefficient remains calibrated until the vacuum line density is derived.
The source roles are limited:

- SST-63 supports boundary determination and protected topological labels;
- SST-23 supports an accelerated torsion/Unruh candidate;
- SST-56 supports line-tangle topology and stability diagnostics.

None of these sources derives a vacuum line density, a per-piercing state
alphabet, or the gravitational area coefficient. The following assumptions
are therefore new Research-Track microstate axioms.

## 2. Microstate assumptions

Let \(\Sigma\) be a locally planar boundary element with unit normal
\(\widehat{\mathbf n}\).

### M1 — Stationary line process

The boundary-relevant SST line fabric is a stationary ergodic collection of
oriented curves with line-length density

\[
\mathcal L_v
=
\lim_{V\to\infty}
\frac{\text{total line length in }V}{\operatorname{Vol}(V)},
\qquad
[\mathcal L_v]=\mathrm{m^{-2}}.
\]

Its tangent orientation probability density is \(f(\widehat{\mathbf t})\),
normalized by

\[
\int_{S^2}f(\widehat{\mathbf t})\,d\Omega=1.
\]

### M2 — Protected piercing alphabet

Each statistically independent boundary piercing carries \(q\ge2\) protected
labels. The entropy capacity per piercing is

\[
s_\ell=\ln q
\]

in nats.

### M3 — Gaussian coherent weak-field cells

The linear torsion excitation on a discretized horizon is represented by a
product of equal-covariance Gaussian microstates. For cell \(j\),

\[
p_{0,j}(x)=\frac{e^{-x^2/2}}{\sqrt{2\pi}},
\qquad
p_{\phi,j}(x)=\frac{e^{-(x-\mu_j)^2/2}}{\sqrt{2\pi}}.
\]

This is the classical probability representation of the coherent-shift sector;
the quantum coherent-state analogue has the same quadratic relative-entropy
structure after canonical mode normalization.

### M4 — Reversible asymptotic boundary encoding

A boundary response encodes the relative distinguishability information using
an asymptotically reversible, capacity-saturating \(q\)-ary code. Thus \(D\)
nats require

\[
\delta N=\frac{D}{\ln q}
\]

activated channels. This is an information-theoretic constitutive assumption;
it is not yet derived from nonlinear Euler/vortex dynamics.

## 3. Piercing-density theorem

A line element \(ds\) with tangent \(\widehat{\mathbf t}\) projects onto
\(\Sigma\) with normal projected measure

\[
dA_\perp
=
|\widehat{\mathbf t}\cdot\widehat{\mathbf n}|\,ds.
\]

Averaging over the stationary line process gives the crossing density

\[
\boxed{
n_\perp(\widehat{\mathbf n})
=
\mathcal L_v
\int_{S^2}
|\widehat{\mathbf t}\cdot\widehat{\mathbf n}|
 f(\widehat{\mathbf t})\,d\Omega.
}
\]

For isotropy,

\[
f=\frac{1}{4\pi},
\qquad
\left\langle|\cos\theta|\right\rangle
=\frac12,
\]

hence

\[
\boxed{
n_\perp=\frac{\mathcal L_v}{2}.
}
\]

Dimensional check:

\[
[n_\perp]=[\mathcal L_v]=\mathrm{m^{-2}}.
\]

## 4. Area-entropy-density theorem

For area \(A\), ergodicity gives

\[
\frac{N_\perp(A)}{A}\longrightarrow n_\perp
\]

in probability, with relative fluctuations vanishing as
\(N_\perp^{-1/2}\) for a Poisson benchmark.

The number of protected label configurations is

\[
W(A)=q^{N_\perp(A)}.
\]

Therefore

\[
S_{\mathrm{cap}}(A)
=\ln W(A)
=N_\perp(A)\ln q,
\]

and

\[
\boxed{
\eta_A^{\mathrm{SST}}
=
\lim_{A\to\infty}\frac{S_{\mathrm{cap}}(A)}{A}
=
n_\perp\ln q.
}
\]

The general anisotropic result is

\[
\boxed{
\eta_A^{\mathrm{SST}}(\widehat{\mathbf n})
=
\mathcal L_v
\left\langle
|\widehat{\mathbf t}\cdot\widehat{\mathbf n}|
\right\rangle_f
\ln q.
}
\]

For isotropy,

\[
\boxed{
\eta_A^{\mathrm{SST}}
=
\frac{\mathcal L_v}{2}\ln q.
}
\]

Dimensional check:

\[
[\eta_A^{\mathrm{SST}}]=\mathrm{m^{-2}},
\]

because \(\ln q\) is dimensionless.

## 5. Boundary-relative-entropy theorem

For equal covariance Gaussians,

\[
D_{\mathrm{KL}}(p_{\phi,j}\Vert p_{0,j})
=\frac{\mu_j^2}{2}.
\]

Discretize the negative horizon generator by midpoint cells
\((U_j,\Delta U,\Delta A)\), and define the coherent microstate shift

\[
\boxed{
\mu_j
=
\sqrt{4\pi(-U_j)\Delta U\Delta A}
\;\partial_U\widehat\phi(U_j).
}
\]

Then

\[
\frac{\mu_j^2}{2}
=
2\pi(-U_j)
\left(\partial_U\widehat\phi(U_j)\right)^2
\Delta U\Delta A.
\]

Because relative entropy is additive for product measures,

\[
\begin{aligned}
\delta S_{\mathrm{boundary}}^{(N)}
&:=
D_{\mathrm{KL}}
\left(
\prod_j p_{\phi,j}
\middle\Vert
\prod_j p_{0,j}
\right)
\\
&=
\sum_j
D_{\mathrm{KL}}(p_{\phi,j}\Vert p_{0,j})
\\
&=
-2\pi
\sum_j
U_j
\left(\partial_U\widehat\phi(U_j)\right)^2
\Delta U\Delta A.
\end{aligned}
\]

In the continuum limit,

\[
\boxed{
\delta S_{\mathrm{boundary}}
=
-2\pi
\int_{\mathcal H^-}
U\,T_{UU}\,dU\,dA
=
S_{\mathrm{rel}},
}
\]

where

\[
T_{UU}
=
(\partial_U\widehat\phi)^2.
\]

### Critical distinction

For equal-covariance shifts,

\[
H[p_{\phi,j}]-H[p_{0,j}]=0,
\]

while

\[
D_{\mathrm{KL}}(p_{\phi,j}\Vert p_{0,j})>0.
\]

Therefore the equality above is an equality of **relative entropy**, not of the
ordinary Shannon/von-Neumann entropy difference. This matches the Dorau--Much
replacement of ill-defined local absolute entropy by relative entropy. A plain
Jacobson-style ordinary entropy increment is not recovered without the
additional boundary-response law below.

## 6. Reversible encoding and area response

By M4, \(S_{\mathrm{rel}}\) nats activate

\[
\delta N
=\frac{S_{\mathrm{rel}}}{\ln q}
\]

boundary channels. Since the crossing density is \(n_\perp\),

\[
\delta A
=\frac{\delta N}{n_\perp}
=\frac{S_{\mathrm{rel}}}{n_\perp\ln q}.
\]

Using \(\eta_A^{\mathrm{SST}}=n_\perp\ln q\),

\[
\boxed{
\eta_A^{\mathrm{SST}}\delta A
=
\delta S_{\mathrm{boundary}}
=
S_{\mathrm{rel}}.
}
\]

This closes the requested algebraic microstate chain under M1--M4.

## 7. Core-tube closure and no-go theorem

For non-overlapping effective tubes of radius \(r_c\), define the occupied
volume fraction \(\varphi_v\le1\). Then

\[
\varphi_v
=\pi r_c^2\mathcal L_v,
\]

so

\[
\mathcal L_v
=\frac{\varphi_v}{\pi r_c^2}.
\]

For isotropy,

\[
\boxed{
\eta_A^{\mathrm{SST}}
=
\frac{\varphi_v\ln q}{2\pi r_c^2}.
}
\]

For the strongest minimal binary model,

\[
\varphi_v=1,
\qquad
q=2,
\]

and the canonical

\[
r_c=1.40897017\times10^{-15}\ \mathrm m
\]

gives

\[
\boxed{
\eta_{A,\max}^{(r_c,q=2)}
=5.557020457583\times10^{28}\ \mathrm{m^{-2}}.
}
\]

Only after this derivation, use the observed Newton constant as an external
audit target:

\[
\eta_A^{\mathrm{GR}}
=\frac{c^3}{4\hbar G}
=9.570182792895\times10^{68}\ \mathrm{m^{-2}}.
\]

Thus

\[
\boxed{
\frac{\eta_A^{\mathrm{GR}}}
{\eta_{A,\max}^{(r_c,q=2)}}
=1.722178794544\times10^{40}.
}
\]

Equivalently, maximal core packing would require

\[
\boxed{
\ln q_{\mathrm{req}}
=1.193723375858\times10^{40}
\quad\text{nats per crossing}.
}
\]

For fixed \(q=2\), the effective transverse channel spacing required by the
observed coefficient is

\[
\boxed{
\ell_{\mathrm{channel}}
=
\sqrt{\frac{\ln2}{\eta_A^{\mathrm{GR}}}}
=2.691241145957\times10^{-35}\ \mathrm m.
}
\]

This last number is an **audit output**, not an input and not an SST derivation
of the Planck scale.

Therefore:

\[
\boxed{
\text{Independent signed }r_c\text{-scale piercings are ruled out as a complete}
\\
\text{microphysical explanation of the gravitational area coefficient.}
}
\]

## 8. Density-weighted candidate

If one additionally assumes that \(\rho_{\!f}\) is a volume average of dense
core tubes in a negligible-density background,

\[
\varphi_v
=\frac{\rho_{\!f}}{\rho_{\mathrm{core}}}
=1.797897875191\times10^{-25}.
\]

Then, for \(q=2\),

\[
\eta_A^{\mathrm{density}}
=9.990955273079\times10^3\ \mathrm{m^{-2}}.
\]

This is even farther from the gravitational target. However, the interpretation
of \(\rho_{\!f}\) as a simple volume average is not canonical and this candidate
is included only as a falsifiable diagnostic.

## 9. What is closed and what remains open

### Closed under explicit assumptions

1. \(n_\perp\) from line length and orientation statistics;
2. \(\eta_A^{\mathrm{SST}}=n_\perp\ln q\);
3. a product Gaussian microstate realization of
   \(\delta S_{\mathrm{boundary}}=S_{\mathrm{rel}}\);
4. the reversible encoding identity
   \(\eta_A^{\mathrm{SST}}\delta A=S_{\mathrm{rel}}\);
5. the no-go result for independent binary core-scale piercings.

### Still open in physical SST

1. derive \(\mathcal L_v\) from the nonlinear substrate vacuum;
2. derive \(q\) and its topological meaning;
3. derive the correlation structure of piercings;
4. derive the reversible channel-activation law dynamically;
5. find a non-ad-hoc mechanism that supplies the missing factor
   \(1.72\times10^{40}\), or accept falsification of this Route-I microstate
   realization;
6. only then continue to the focusing tensor and Poisson-limit tests.

## 10. Falsifiers

The model is falsified if any of the following occurs:

- crossing number fails to be asymptotically extensive in area;
- the boundary state does not factorize or possess a finite correlation length;
- coherent weak-field excitations do not reduce to equal-covariance Gaussian
  shifts;
- the relative entropy fails to converge to the modular energy flux;
- no independently derived \(\mathcal L_v\), \(q\), or correlated degeneracy
  reproduces the required area density;
- the resulting \(\eta_A^{\mathrm{SST}}\) is state-, orientation-, or
  species-dependent where universality is required.

## References

```latex
\begin{thebibliography}{9}

\bibitem{DorauMuch2026}
P.~Dorau and A.~Much,
\newblock From quantum relative entropy to the semiclassical Einstein equations,
\newblock \emph{Physical Review Letters} \textbf{136}, 091602 (2026).
\newblock doi:10.1103/lmq8-nsty.
\newblock arXiv:2510.24491.

\bibitem{KullbackLeibler1951}
S.~Kullback and R.~A.~Leibler,
\newblock On information and sufficiency,
\newblock \emph{Annals of Mathematical Statistics} \textbf{22}, 79--86 (1951).
\newblock doi:10.1214/aoms/1177729694.

\bibitem{HiaiPetz1991}
F.~Hiai and D.~Petz,
\newblock The proper formula for relative entropy and its asymptotics in quantum probability,
\newblock \emph{Communications in Mathematical Physics} \textbf{143}, 99--114 (1991).
\newblock doi:10.1007/BF02100287.

\bibitem{Shannon1948}
C.~E.~Shannon,
\newblock A mathematical theory of communication,
\newblock \emph{Bell System Technical Journal} \textbf{27}, 379--423 and 623--656 (1948).
\newblock doi:10.1002/j.1538-7305.1948.tb01338.x;
10.1002/j.1538-7305.1948.tb00917.x.

\bibitem{Crofton1868}
M.~W.~Crofton,
\newblock On the theory of local probability,
\newblock \emph{Philosophical Transactions of the Royal Society of London}
\textbf{158}, 181--199 (1868).
\newblock permalink:https://www.jstor.org/stable/108911.

\bibitem{Jacobson1995}
T.~Jacobson,
\newblock Thermodynamics of spacetime: The Einstein equation of state,
\newblock \emph{Physical Review Letters} \textbf{75}, 1260--1263 (1995).
\newblock doi:10.1103/PhysRevLett.75.1260.

\end{thebibliography}
```
