# QGI phase-data pipeline

The experiment reports population-vs-interferometer-duration data and obtains phase through a
nonlinear fringe fit.

v0.2.0 implements the published structure:

\[
P(t)
=
P_{\rm mean}(t)
+\frac12 V(t)\cos\phi(t),
\qquad
\phi(t)=c_0+c_1t+c_2t^2+c_3t^3.
\]

For raw population data:

1. local extrema are detected;
2. upper and lower envelopes are fitted;
3. a seventh-order polynomial is used by default;
4. the oscillation is normalized;
5. an FFT Hilbert transform supplies an initial unwrapped phase;
6. a cubic phase is fitted;
7. the first and last oscillation are excluded;
8. a damped Gauss-Newton fit is performed directly on population.

The final specific action is

\[
\frac{h}{m}
=
\frac{\pi g_{\rm eff}^2}{12|c_3|}.
\]

No \(m\), \(h\), or \(\hbar\) is passed to this calculation.

## Data grades

`RAW_POPULATION_CSV`
: strongest branch; may generate a primary QGI data PASS.

`PUBLISHED_FIGURE3_DATA_FIT_DIGITIZED`
: public figure-derived fallback; `CONDITIONAL`.

`SYNTHETIC_TEST_ONLY`
: unit-test/calibration only; excluded from scientific verdict.

The package intentionally has no category named `RAW` for data digitized from a publication figure.
