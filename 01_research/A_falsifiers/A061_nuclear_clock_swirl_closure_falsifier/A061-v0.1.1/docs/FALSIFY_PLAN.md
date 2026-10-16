# A061 falsification protocol — 0.1.0 frozen

## Research question

Can SST-28 plus a separately derived PKLSA/delay model predict an observable Th-229 vs Yb+ **differential fractional frequency time series** or a crystal-to-crystal invariant which cannot be accounted for by (a) known environmental line-center shifts, (b) measured instrument feedback or (c) stochastic clock noise?

## Models

- **H0A**: common time scaling `S(x,t)` multiplies both oscillators at the same event. Differential `d ln(f_Th/f_Yb)` contribution identically zero. This is a structural identifiability null, not a numerical fit.
- **H0B**: species-specific nuclear/electronic transition energies depend on known environmental variables; frequency shifts in independent crystals need not be identical; no SST coupling.
- **H0C**: external phase-locked laser/cavity feedback plus shot and environmental noise may induce finite frequency-domain features. No internal vortex dynamics.
- **H1**: species-dependent effective clock response `S_i` exists and independently determined SST equations predict `delta ln S_Th - delta ln S_Yb` with a sign, amplitude, frequency range and associated uncertainties. No free parameter may be tuned on test data.
- **H2**: topological plateau or transport-delay branch predicts quantized or oscillatory frequency shifts. Winding labels/branch IDs must be specified from independently qualified knots before observing the clock spectra.

## Operational observables

`y(t)=8*(f_beat_IR(t)-mean(f_beat_IR)) / f_Th`, without further application of the frequency factor 8 if source file is already VUV-shifted. Use raw metadata for frequency sign/origin. `delta ln(fTh/fYb)` approx `y(t)` only in small-signal limit, after accounting for local reference behavior and correct extraction of f_beat sign. These approximations remain a **calibration gate**.

The Huang paper provides an intercrystal line-b offset and noise slopes. Use it to constrain environmental noise models, not to substitute for a synchronized Th/Yb timing comparison. Absolute frequency uncertainty and between-sample differential uncertainty may share correlated parts and must be propagated using covariance.

## Gate interpretation

- **G00** provenance and freeze. `PASS` only for hash integrity / source identification.
- **G01** published numeric reproduction, not native raw analysis.
- **G02** pure common-mode cancellation. A PASS **rules out identifiability of a universal S via a ratio**; it does not support H1.
- **G03** SST-28 consistency audit; zero vorticity vs local tangential velocity, smooth profile vs thin-core singular plateau, n-winding admissibility. Can FAIL independently of any experimental data.
- **G04** fit identifiability check across crystals. With two environmental offsets and no independent environment transfer coefficient, report `INCONCLUSIVE`; never claim SST effect from observed offset.
- **G05** delayed external optical feedback synthetic controls; check spurious peaks; `PASS` certifies that code detects the instrumental alternative.
- **G06** actual Toscani center-beat CSV prerequisite. A global periodogram with block-bootstrap null and explicit frequency trials. A detected peak is a candidate instrumental/physical periodicity, not SST confirmation. Test stationarity, autocorrelation and aliases with longer-term investigations.
- **G07** strict physical prediction gate: require independent PKLSA geometry -> clock susceptibility -> nuclear/electronic sensitivity; should be calculated, uncertainty-propagated and sealed *before* accessing holdout. The absence of coefficients is not a failed theory prediction; it is `INCONCLUSIVE`.
- **G08** cross-laboratory replication requires compatible simultaneously time-resolved independent measurements of the same candidate modulation, and common reference/time metadata. Published crystal means do not suffice.
- **G09** independent C++17 FP64 numerical parity of exact dimensionless profile kernel, not a physics gate.

A downstream gate runs even when an upstream gate failed. Gate statuses from different evidence classes (`mathematical_identity`, `synthetic_control`, `published_summary`, `experimental_raw`) may **never** be summed into a support vote.

## Key risk factors / edge cases

- Label leakage, post-hoc phase/frequency selection, absolute vs differential drift, correlated systematics, clock instrumental servo transfer function, nonstationarity and drifting shot-noise amplitude, laser-induced nuclear quenching, crystal strain, magnetic and thermal shifts, irregular sampling aliasing, shared lab reference errors, paper revisions with differing source-data versions.
- For the SST-28 ansatz, near the axis `S->1`; at infinity `S->1`; at `x=1` the minimum is `sqrt(1-e^-2)`. Circulation-pole model diverges inside `x<|n|` (non-real S), so a thin-core regularization must be independently specified before closure.

## Minimal new experiment

Simultaneously interrogate at least two distinct nuclear/electronic clock systems under controlled, **independently calibrated variations in the same physical vortex observable**, with additional common-mode controls and precommitted SST response coefficients. No presently provided physical experiment measures a medium vorticity proxy directly; absent such an observable, a zero result constrains only a phenomenological clock-coupling amplitude rather than a unique SST mechanism.
