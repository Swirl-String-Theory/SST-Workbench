# F005 v0.4.3 - Science contract (development, non-blind)

## Inputs, scope and prohibitions

- Robot sloshing dataset: 9,822 trajectories x 1,500 samples; acceleration [m/s^2], wall elevation [mm]; sampling interval dt=0.004 s.
- The original `STANDARD_TRAIN` (3,500) and `STANDARD_VALIDATION` (750) together form a **reused** DEVELOPMENT population of 4,250. Historical validated outcomes cannot become unseen holdouts retroactively.
- `STANDARD_TEST` (750) and `OPTIMIZED_OOD` (4,822) measured elevations are never indexed, fingerprinted or scored in v0.4.3. Their input accelerations may have been used in the historical v0.4.2 candidate screen; the NEW development graph restricts edges to development-only nodes. Do not open `DATASET.zip` (49.9GB).
- Lock v0.4.2 report, input array hash, accepted-edge SHA256, and metadata/split consistency through historical v0.3 source lock. Historical packages and results remain unchanged.

## P5d - candidate graph, not source family independence

Build connected components from `v0.4.2/family_candidate_matches_REVIEW.csv` edges **when both endpoints are in DEVELOPMENT**. Each previously accepted edge must have correlation >= 0.995 and normalized RMSE <= 0.075 with allowable shifts {-4,-2,0,+2,+4} source samples. Independently spot-check sampled edges. Count, hash and retain the edge list. Use seeded group assignment (20261020) with nominal 20% validation, without reading elevation outcomes. Components are indivisible.

**Pass in the candidate graph** means zero detected cross-partition edges and no shared component ID across the new groups. It does *not* imply exhaustive waveform-family separation, publisher-defined family IDs, or independent physical replicates. Graph transitivity can overmerge shapes and missing candidates can undermerge.

## P6h - newly trained conditional ARX predictor

For newly assigned TRAIN only, identify via second differences:

\[\eta_{n+1} = A\eta_n+B\eta_{n-1}+C\,a_n\Delta t^2.\]

Units: elevation eta in metres; acceleration a in m s^-2; time in seconds; A, B, C dimensionless. No reuse of v0.3 ARX coefficients when fitting. Fail closed on unstable identified discrete poles. No fitted parameters depend on new validation output.

At each predeclared anchor t0 = 0.004, 1.5, 2.8 s, exactly two measured elevations are supplied as initial conditions. For horizons 0.1, 0.5, 1, 2, 3 s, feed recursively predicted elevations and the known measured **future acceleration**. Do not inject any measured elevation within forecast horizon.

Scores: full-path RMSE and endpoint RMSE in mm. Controls: persistence, linear extrapolation, zero response, independently fitted driven oscillator. No evaluation of original TEST/OOD responses.

## P6i - independent TRAIN-only reduced oscillator

On TRAIN segments selected solely by low applied acceleration and minimum visible water-elevation signal, identify:

\[\ddot\eta + 2\gamma\dot\eta+\omega_0^2\eta = K a(t).\]

Dimensional checks: gamma [s^-1], omega0 [s^-1], K dimensionless. Estimate gamma and omega0 from free-ringdown samples using centered differences; estimate K separately from TRAIN forced residuals. This is an **independently fitted reduced model**, not a parameter-free physics prediction and not a numerical solution of the 3D Euler equations. Reject insufficient ringdown, nonpositive gamma, or omega0² <= gamma²; do not reuse former ARX poles.

Discretize with centered damping:

\[(1+\gamma\Delta t)\eta_{n+1}=(2-\omega_0^2\Delta t^2)\eta_n-(1-\gamma\Delta t)\eta_{n-1}+K\Delta t^2a_n.\]

Group-bootstrap uncertainty: resample **proxy components**, not individual trajectories (250 draws, seed 20261020). Report per-baseline intervals without promoting best-selected baseline intervals to confirmatory conclusions. Test for both path and endpoint errors. Any oscillator fit failure must be reported as BLOCKED with incomplete baseline qualification.

## Falsification / qualification gates

- P5d = proxy-disjoint graph audited, source-defined family IDs absent -> **DEVELOPMENT / true independence UNRESOLVED**.
- P6h = ARX re-fit plus free recursive forecast, report performance without promotion based on wins alone.
- P6i = independent TRAIN-only oscillator identification, independent of old ARX poles but dependent on the same reused dataset.
- P7 = Euler/PKLSA **NOT RUN**; P8 = SST physical claims **UNRESOLVED**.

Run synthetics first. No AI/paper claim about validated physics is licensed by positive reduced-model predictions.

## References (LaTeX)

```latex
\bibitem{Giulietti2026}
Giulietti et al.,
``Robot-executed sloshing dataset,''
Zenodo (2026), \url{https://doi.org/10.5281/zenodo.20039757}.

\bibitem{Ljung1999}
L.~Ljung, \emph{System Identification: Theory for the User},
2nd ed., Prentice Hall (1999), ISBN 9780136566953.
```
