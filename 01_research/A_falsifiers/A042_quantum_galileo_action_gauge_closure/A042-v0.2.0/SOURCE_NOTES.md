# Source notes — Dobkowski et al. (2026)

The package uses the following source-level statements from the QGI paper:

1. The Newtonian-to-Einsteinian wavefunction transformation contains the gauge phase
   \[
   \phi_{\rm gauge}(z,t)
   =\frac{m}{\hbar}\left(-\frac16g^2t^3-gzt\right).
   \]

2. In the symmetric QGI geometry,
   \[
   \Delta\phi=-\frac{m g^2T^3}{3\hbar}.
   \]

3. With a reference-arm acceleration \(a\),
   \[
   \Delta\phi=\frac{ma(a-2g)}{3\hbar}T^3.
   \]

4. The measured phase may be represented as the action of the ballistic path in the
   Newtonian frame or equivalently through the freely-falling-frame description.

5. The reported blind numerical simulation differs from the data by about 2.5% over
   roughly 80 rad, and the paper states an upper limit of a few percent on deviations
   from the predicted prefactor.

6. The authors explicitly note that models violating the equivalence principle are not
   all excluded, because some could predict the same phase.

This package therefore treats QGI as a closure target, not unique evidence for SST.
