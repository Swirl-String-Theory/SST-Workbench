# Feasibility report

## Verdict

\[
\boxed{\text{D0 partially fails, while the mathematical and numerical rod project remains feasible.}}
\]

The public literature supplies energies, topology labels, figures, analytic
axial circles and initial-field constructions, but not a complete
machine-readable catalogue of relaxed centreline and framing data. A full
\(Q=1,\dots,16\) fit therefore requires either author-supplied data or an
independent field/rod reconstruction campaign.

---

## 1. Machine-readable centrelines and framings

### Publicly reconstructible now

The HSS axial solutions are completely specified analytically:

\[
\gamma_Q(\theta)=b_Q(\cos\theta,\sin\theta,0),\qquad
b_Q=\sqrt{1+C Q^2},
\]

\[
L_Q=2\pi b_Q,\qquad
\alpha(s)=\frac{2\pi Q}{L_Q}s .
\]

Therefore \(Q=1,2\), and the unstable axial continuation for higher \(Q\), can
be generated machine-readably without external files.

HSS also publishes numerical energies for the first buckled rods, links and
trefoils, and explains the numerical method: a 100-vertex polygon, simulated
annealing, equal-edge penalty, curvature bound, pair-separation constraint and
twist measured relative to a Bishop frame. These descriptions prove
reproducibility in principle, but do not specify the final vertex and material
frame arrays.

Sutcliffe 2007 publishes the energy/type catalogue and rational-map families
used to create initial fields. These formulas can reproduce seeds, not the final
relaxed three-dimensional fields or their antipodal preimage centrelines.

### Not located in the public record searched

No attached machine-readable files were located for:

- final HSS non-axial polygon vertices;
- HSS material-frame/Bishop-angle data;
- final Sutcliffe 2007 lattice fields;
- extracted antipodal preimage centrelines;
- framing/preimage companion curves for all catalogue entries;
- the exact simulation/annealing source used in those two papers.

An exact-title GitHub code search returned only bibliographic metadata rather
than a scientific source repository.

### Existing ideal-knot data are not substitutes

Ideal-knot Fourier, polygonal or Ridgerunner data can seed knot sectors, but
they are not the HSS elastic-rod minima or the Skyrme–Faddeev preimage curves.
They also do not determine the HSS material framing.

### D0 status

\[
\boxed{
\begin{array}{ll}
Q=1,2\text{ axial circles} & \text{available analytically},\\
Q=3,\dots,7\text{ HSS non-axial rods} & \text{must be regenerated or requested},\\
Q=1,\dots,16\text{ SF final centrelines/frames} & \text{must be regenerated or requested}.
\end{array}}
\]

The cheapest next action is a concise data request to the three HSS authors,
followed in parallel by an independent rod reimplementation.

---

## 2. Near-diagonal subtraction

For components \(\gamma_\mu:[0,L_\mu]\to\mathbb R^3\), define

\[
\mathcal N_a
=
\frac12\sum_{\mu,\nu}
\int_0^{L_\mu}\!\!\int_0^{L_\nu}
\frac{\mathbf t_\mu(s)\cdot\mathbf t_\nu(s')}
{\sqrt{|\gamma_\mu(s)-\gamma_\nu(s')|^2+a^2}}
\,ds\,ds'.
\]

The same-component diagonal contains the local line contribution already
represented by the HSS length, curvature and twist terms. Let

\[
d_{L_\mu}(s,s')
=
\min\{|s-s'|,L_\mu-|s-s'|\}
\]

be periodic arclength distance and choose a subtraction range
\(0<\ell_{\rm sub}\le L_\mu/2\). A sharp-window baseline is

\[
\boxed{
\mathcal N^{\rm ren}_{a,\ell_{\rm sub}}
=
\mathcal N_a
-
\frac12\sum_\mu
\int_0^{L_\mu}\!\!\int_0^{L_\mu}
\frac{\mathbf 1_{d_{L_\mu}(s,s')<\ell_{\rm sub}}}
{\sqrt{d_{L_\mu}(s,s')^2+a^2}}
\,ds\,ds' .
}
\]

The subtraction for component \(\mu\) is

\[
L_\mu\operatorname{arsinh}\!\left(\frac{\ell_{\rm sub}}a\right).
\]

Near \(u=s'-s=0\),

\[
|\gamma(s+u)-\gamma(s)|^2
=
u^2-\frac{\kappa^2u^4}{12}+O(u^5),
\]

\[
\mathbf t(s)\cdot\mathbf t(s+u)
=
1-\frac{\kappa^2u^2}{2}+O(u^3),
\]

so in the \(a\to0\) limit the subtracted integrand behaves as

\[
-\frac{11}{24}\kappa^2|u|+O(u^2),
\]

which is integrable.

Changing \(\ell_{\rm sub}\) shifts the answer by a term proportional to total
length. Therefore the line-tension coefficient and the subtraction convention
must be fitted or matched together. The separated quantities are
scheme-dependent; total energies are the observables.

For publication a smooth compactly supported window should replace the sharp
indicator. The sharp scheme is retained here because it has a transparent
analytic circle value.

---

## 3. Circle value

For a circle of major radius \(b\),

\[
\gamma(\theta)=b(\cos\theta,\sin\theta,0),\qquad L=2\pi b,
\]

the raw signed Neumann-type functional is

\[
\boxed{
\mathcal N_a^\circ(b)
=
\frac{2\pi}{\sqrt{a^2+4b^2}}
\left[
(a^2+2b^2)K(m)
-
(a^2+4b^2)E(m)
\right],
}
\]

where \(K,E\) are complete elliptic integrals and

\[
m=\frac{4b^2}{a^2+4b^2}.
\]

The sharp-window renormalized value is

\[
\boxed{
\mathcal N_{a,\ell_{\rm sub}}^{\circ,\rm ren}(b)
=
\mathcal N_a^\circ(b)
-
2\pi b\,
\operatorname{arsinh}\!\left(\frac{\ell_{\rm sub}}a\right).
}
\]

For the global periodic subtraction
\(\ell_{\rm sub}=L/2=\pi b\),

\[
\mathcal N_{a,\rm global}^{\circ,\rm ren}
=
\mathcal N_a^\circ
-
2\pi b\,\operatorname{arsinh}\!\left(\frac{\pi b}{a}\right).
\]

As \(a/b\to0\),

\[
\mathcal N_a^\circ
=
2\pi b\left[\log\!\left(\frac{8b}{a}\right)-2\right]
+o(b),
\]

and the global-subtraction limit becomes

\[
\mathcal N_{\rm global}^{\circ,\rm ren}
\longrightarrow
2\pi b\left[\log\!\left(\frac4\pi\right)-2\right].
\]

The supplied script compares the elliptic-integral expression to direct
quadrature.

---

## 4. Rank of \(C\)-\(g\) identifiability on \(Q=1,2\)

For an axial circle of radius \(b\), the provisional extended model is

\[
E_Q(b;C,g)
=
2\pi\left[
b+\frac{1+CQ^2}{b}
\right]
+
g\,\mathcal N^{\circ,\rm ren}_a(b).
\]

After \(Q=1\) fixes energy and length scales, the \(Q=2\) energy ratio alone is
one scalar observation:

\[
y_E=\frac{E_2}{E_1}.
\]

Its Jacobian with respect to \((C,g)\) is \(1\times2\), hence

\[
\boxed{\operatorname{rank}J_E\le1.}
\]

It cannot identify two parameters.

If the independent \(Q=2\) length ratio is also used,

\[
\mathbf y=
\left(
\frac{E_2}{E_1},
\frac{L_2}{L_1}
\right),
\]

the Jacobian can be rank two. For the explicit global-subtraction baseline

\[
C=0.85,\qquad g=0,\qquad a=R=1.36,
\]

the numerical Jacobian is approximately

\[
J=
\begin{pmatrix}
0.28419 & -0.10148\\
0.28529 & -0.01437
\end{pmatrix},
\]

with

\[
\det J\simeq2.49\times10^{-2},\qquad
\operatorname{rank}J=2,\qquad
\kappa_2(J)\simeq6.8.
\]

Thus energy plus length is locally sufficient in this specific scheme.

There are two cautions:

1. the \(Q=1\) circle lies almost exactly on the active thickness constraint,
   making derivatives convention-sensitive;
2. the subtraction scale shifts the line coefficient, so rank must be
   recomputed after the final renormalization convention is frozen.

As a diagnostic only, fitting the quoted HSS/SF ratios
\((E_2/E_1,L_2/L_1)=(1.63,1.45)\) in this baseline gives an unconstrained
solution near

\[
C\simeq1.167,\qquad g\simeq-0.249,
\]

outside Michell's interval. Constraining

\[
1/\sqrt3<C<\sqrt3/2
\]

cannot match both ratios in this baseline. This is not yet a falsification of
all non-local models; it is an early warning that the signed kernel and
renormalization convention are nontrivial.

---

## 5. Independent sector relaxation

### Technical feasibility

Yes. HSS already demonstrated the essential algorithm for separate axial,
buckled, link and trefoil sectors:

- polygonal centrelines;
- fixed-thickness constraints;
- curvature constraints;
- pair-separation constraints;
- simulated annealing;
- Bishop-frame twist evaluation.

The new non-local term adds an \(O(N^2)\) pair sum. For \(N=100\)–\(500\)
vertices and a few dozen sectors this is computationally modest. C++/pybind is
useful but not required for the feasibility phase.

### Required state

For each component store:

\[
\{\mathbf x_i,\ \beta_i,\ q_i\},
\]

where \(\mathbf x_i\) are vertices, \(\beta_i\) is the material-frame angle
relative to a discrete Bishop frame, and \(q_i\) is the component twist/Hopf
allocation.

### Topology policy

Hard thickness preserves component number and isotopy class. Therefore a rod
relaxer cannot reproduce

\[
K_{3,2}\to L
\]

as a continuous relaxation. Instead minimize each sector independently and
compare energies.

For \(Q=5,6,7\), the preregistered comparison is

\[
E_{\rm link}<E_{K_{3,2}}\quad(Q=5,6),
\qquad
E_{K_{3,2}}<E_{\rm link}\quad(Q=7).
\]

For \(K_{5,2}\), continue the same knot sector through twist/Hopf allocations
\(Q=8,9,10,11\) and test local stability using repeated starts and a projected
Hessian or negative-mode search.

### Main numerical risks

- active-set changes in the thickness constraints;
- frame holonomy and integer twist bookkeeping;
- local-minimum dependence on seeds;
- orientation dependence of the signed kernel;
- double counting if the subtraction and HSS local coefficients are not
  matched together.

### Feasibility verdict

\[
\boxed{
\text{sector relaxation is feasible; catalogue reconstruction, not optimization, is the bottleneck.}
}
\]

---

## Recommended decision

1. Send the data request.
2. Freeze one subtraction scheme and validate the circle formula.
3. Reproduce HSS \(Q=1,\dots,7\) without the new term.
4. Only then add the non-local operator.
5. Treat energy and length jointly; energy alone cannot identify \(C,g\).
6. Do not begin the \(Q=8,\dots,16\) campaign until the \(Q\le7\) baseline
   reproduces the published sector ordering.

## Primary references

- P. Sutcliffe, “Knots in the Skyrme–Faddeev model,” Proc. R. Soc. A 463,
  3001–3020 (2007), doi:10.1098/rspa.2007.0038, arXiv:0705.1468.
- D. Harland, J. M. Speight and P. M. Sutcliffe, “Hopf solitons and elastic
  rods,” Phys. Rev. D 83, 065008 (2011),
  doi:10.1103/PhysRevD.83.065008, arXiv:1010.3189.
- P. G. Saffman, *Vortex Dynamics*, Cambridge University Press (1992).
