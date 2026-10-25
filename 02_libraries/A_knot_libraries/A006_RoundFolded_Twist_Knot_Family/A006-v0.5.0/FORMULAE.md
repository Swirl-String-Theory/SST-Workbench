# VCCR v0.1.0 — equations, units and limitations

For a non-self-overlapping, circular *material* vortex tube with a uniform cross-sectional area `A` along its axis:

$$
V=A L=\pi a^2L,\qquad [V]={\rm m^3},\ [a]=[L]={\rm m}.
$$

With conserved `V` and a reference state `(a0,L0)`:

$$
\boxed{a(L)=a_0\left(\frac{L_0}{L}\right)^{1/2}.}
$$

Under Kelvin/Helmholtz conditions, Γ is conserved; with uniform axial mean vorticity and circular cross-section:

$$
\Gamma=\overline\omega\pi a^2,\quad
\overline\omega(L)=\frac{\Gamma L}{V},\quad
v_\phi(a)=\frac{\Gamma}{2\pi a}.
$$

Dimensional check: `[Gamma]=m²/s`, `[omega]=1/s`, `[v_phi]=m/s`.

Define *diameter-convention* ropelength `R_d=L/(2a)`. **Literature frequently uses `R_a=L/a=2R_d`.** Since `L=2aR_d`, then:

$$
\boxed{V=2\pi R_d a^3,\quad a=\left(\frac{V}{2\pi R_d}\right)^{1/3},\quad L=2 a R_d.}
$$

At fixed `V`, higher actual `R_d` means lower `a`; but *this relation uses physical effective core a, not just a geometrical polygon thickness*. The geometric ropelength `L / (2 a_geo)` only determines `a` if we additionally impose `a_core=a_geo` (tube-saturation hypothesis).

For an independently certified minimum ropelength `R_min,d(K)` and an actual uniform embedded physical tube, `R_actual,d ≥ R_min,d(K)` implies:

$$
\boxed{L\geq (4V R_{\min,d}^2/\pi)^{1/3},\quad a\leq (V/(2\pi R_{\min,d}))^{1/3}.}
$$

A numerical optimizer returns a candidate upper bound for the true unknown minimum; **it cannot be substituted without qualification for an independently established lower bound** when claiming a necessary inequality. Hence the CLI `bounds` output is labeled conditional, not a rigorous bound unless input truly qualifies.

Local Lagrangian segment model with material segment stretch `lambda_i=dl_i(t)/dl_i(0)`:

$$
A_i(t)=A_i(0)/\lambda_i,\quad
 a_i(t)=a_i(0)/\sqrt{\lambda_i},\quad
 \overline\omega_i(t)=\overline\omega_i(0)\lambda_i.
$$

**Time-evolving full Euler fields, cross-sectional shape, and material correspondence are not computable from two arbitrary XYZ curves alone.** The `compare` command demands an explicit operator assertion, and still labels material correspondence unverified.

For the SST numerical trefoil reference (**conditional**):

$$
\begin{aligned}
  r_c&=1.40897017\times10^{-15}\,\mathrm{m},\\
  \left|\mathbf v_{\!\boldsymbol{\circlearrowleft}}\right|&=1.09384563\times10^6\,\mathrm{m\,s^{-1}},\\
  R_{d,0}&=16.3714672385,\\
  L_0&=2r_cR_{d,0}=4.6133817956357553\times 10^{-14}\,\mathrm m,\\
  V_0&=\pi r_c^2L_0=2.877218654223102\times10^{-43}\,\mathrm{m^3},\\
  \Gamma_0&=2\pi r_c\left|\mathbf v_{\!\boldsymbol{\circlearrowleft}}\right|=9.683619203488876\times10^{-9}\,\mathrm{m^2/s}.
\end{aligned}
$$

The `R_d,0` figure is a numerical reference, not an exact invariant, and physical core filling is postulated. Different knotted tubes cannot be assigned equal V without an additional explicit assumption.