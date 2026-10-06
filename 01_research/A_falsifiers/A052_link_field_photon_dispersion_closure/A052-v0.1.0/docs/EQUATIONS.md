# Equations

For a frozen dynamical eigenbranch \(\omega(k)\), the group velocity is

\[
 v_g(k)=\frac{d\omega}{dk}.
\]

For discrete samples, the interior estimator is the centered finite difference

\[
 v_{g,i}\simeq\frac{\omega_{i+1}-\omega_{i-1}}{k_{i+1}-k_{i-1}}.
\]

The A044 transfer quantity is

\[
 \delta_i = 1-\frac{v_{g,i}}{c}.
\]

A power-law diagnostic may be computed only after \(\delta_i\) exists independently:

\[
 n_{\rm eff}=\frac{d\ln\delta}{d\ln E}.
\]

No value of \(n_{\rm eff}\) or an effective LIV scale is used in A052 as an input target.
