# F005 v0.5.0-p2 — Evidence contract and gates

## Fixed science contract

- `P2_LOCKED_DEVELOPMENT_SPLIT`: SHA-256 must exactly equal `d60bfe0daa8195290958ca0b8f6268e01bf93811267e6c80b02cfadaa84d37a2`; only original TRAIN+VALIDATION proxy groups permitted, with exactly 3,400 DEV_TRAIN, 850 DEV_VALIDATION and no cross-group ID in the *registered* graph.
- `P2_GEOMETRY_SOURCE`: exact documented thesis geometry, water-model parameters, right-hand wall. Capillary coefficient sigma=0 is a declared approximation and is **not** a physical measurement of zero surface tension.
- `P2_STATIC_ACQUISITION_CODE`: candidate references to axis transforms, signs, frame flips, height equation, pre-motion synchronization. Never execute third-party Python or other source.
- `P2_INPUT_AXIS`, `P2_HEIGHT_AXIS`: proposed +/-1 values with original source SHA-256 and *human-authenticated physical mapping from raw robot/camera coordinates to exported NPY*. Verifying bytes and lines is not verifying semantic physical truth.
- `P2_PREMOTION_RAW`: per-row provenance, corresponding raw trace SHA-256, timestamps strictly increasing, a declared first-motion time and at least 1000 earlier scalar samples. Failure is a blocker; passing is a *scalar-observation screen only*.
- `P2_HYDRODYNAMIC_REST`: not derivable from one scalar free-surface time series. To certify a full Euler-from-rest prediction, supply independent field or a defensible protocol-specific physical rest bound. No automatic PASS.
- `P2_PROVENANCE_ATTESTATION`: blocked until provenance semantics and applicable rest conditions are independently reviewed and documented.
- `E0_MAIN_EULER_GATE`: deliberately BLOCKED regardless of scanner success; do not mutate previous config, release, outputs or prior manifests.

### Distinguishing source facts, statistical tests and hypotheses

- The thesis's `1,000` pre-motion camera samples are used for optical baseline subtraction; this does not imply the released arrays include all those samples.
- A comparison of theoretical Euler outputs and measured TRAIN heights identifies at most a **relative sign convention** and was already performed in p1. p2 never fits a physical parameter or selects sign by RMSE.
- The source density `998 kg/m3` is the *model* value in Table 2.1 for a water-like coffee mixture. `sigma=0` is a model approximation; a capillary sensitivity analysis is separate.
- A source-native Euler solution for rest state should not be called experimentally validated until the geometry, sign mapping and initial-state assumptions are all independently evidenced.

### Mathematical identifiability

Given any linear scalar map with physical acceleration $a$ and height $\eta$,

$$\eta_{\mathrm{observed}}(t)=s_{\eta}\,\mathcal L[s_a\,a_{\mathrm{raw}}](t),\qquad s_\eta,s_a\in\{-1,+1\}.$$

For a linear map $\mathcal L$ the signals constrain $s_\eta s_a$, **not both signs independently**.

$$\eta(0)=0,\quad\dot\eta(0)=0\quad\not\Rightarrow\quad\mathbf v(\mathbf x,0)=\mathbf 0.$$

Even 1,000 pre-motion free-surface samples can only screen the *surface observable*.

### Source bibliography (copy-ready)

```latex
\bibitem{Camilotto2026}
D. Camilotto,
``A Comprehensive Data-Driven Framework for Robotic Liquid Sloshing Control:
From Extensive Experimental Model Validation and Enhancement to Trajectory Optimization,''
Master's thesis, Politecnico di Milano (2026).
\url{https://hdl.handle.net/10589/253216}.

\bibitem{FaltinsenTimokha2009}
O. M. Faltinsen and A. N. Timokha,
\emph{Sloshing}, Cambridge University Press (2009).
ISBN 9780521881111.
```

