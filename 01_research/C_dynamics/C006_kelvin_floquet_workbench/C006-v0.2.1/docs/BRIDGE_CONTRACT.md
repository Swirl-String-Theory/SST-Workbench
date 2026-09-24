# Preregistered \(P_{\rm BS}\) contract

Frozen in `THRESHOLDS_FROZEN.json` before any scientific trajectory.

## Scientific amplitude

\[
a_m^{\rm raw}(t)=p_m^\dagger W_r B\,\Pi_{m,k}\,P_{\rm BS}[\delta X(t)],
\qquad
p_m^\dagger W_r B q_m=1.
\]

\(q_m^\dagger B\) is diagnostic only. Do not fall back to it.

\(W_r\) is Clenshaw–Curtis on the A029 Chebyshev–Lobatto nodes times the cylindrical Jacobian \(r\).

## Forbidden inputs

`prediction_inputs_consumed = []`

The producer must not consume \(\omega_{\rm pred}\), \(v_g\), \(L/|v_g|\), \(\Phi_{\rm pred}\), \(e^{\lambda t}\), or `expm(B^{-1}A)`.

## Provenance order

frozen geometry → mode reconstruction cert → tube validity cert → bridge qualification → raw timeseries.

## Data split

\(D_{\rm bridge}=\{\text{C006 unit ring},\ \texttt{c1630473578eb8fa}\}\)

\(D_{\rm score}=\varnothing\) in this release. Do not score M0–M3.

## Tube gate

\(a r_{\max}\kappa_{\max}<c_\kappa\) and \(2 a r_{\max}<c_d\,d_{\min,\rm nonlocal}\).

On failure emit `INDETERMINATE_TUBE_CHART_INVALID`. Never shrink \(r_{\max}\).
