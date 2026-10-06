# Mathematical specification

For two complex amplitudes \(\eta_1,\eta_2\), define

\[
\chi_T=\frac{2\,\mathrm{Im}(\eta_1^*\eta_2)}{|\eta_1|^2+|\eta_2|^2+\varepsilon}.
\]

Properties used by the falsifier:

\[
\eta_j\rightarrow e^{i\theta}\eta_j\quad\Rightarrow\quad\chi_T\rightarrow\chi_T,
\]

and, for the default antiunitary representation,

\[
\eta_j\rightarrow\eta_j^*\quad\Rightarrow\quad\chi_T\rightarrow-\chi_T.
\]

The weighted relative-phase order parameter is

\[
Z_{12}=\frac{\sum_t w_t e^{i\arg(\eta_2\eta_1^*)}}{\sum_t w_t},
\qquad R_{12}=|Z_{12}|,
\]

\[
w_t=\frac{2|\eta_1||\eta_2|}{|\eta_1|^2+|\eta_2|^2+\varepsilon}.
\]

`R12 -> 1` indicates a concentrated relative phase; it does not by itself establish a physical material phase.

## Reversible synthetic reference

Instrument qualification uses the Hamiltonian

\[
H(\phi,p)=\frac{p^2}{2}+\frac{\kappa}{2}\cos(2\phi),\qquad \kappa>0,
\]

with

\[
\dot\phi=p,\qquad \dot p=\kappa\sin(2\phi).
\]

Its stable phase branches are at \(\phi=\pm\pi/2\). The antiunitary time-reversal representation is

\[
\mathcal T:(\phi,p,t)\mapsto(-\phi,p,-t),
\]

which exchanges the two degenerate branches. This model is a test fixture only; it is not an SST dynamical model and is excluded from the physical verdict.
