# A006 Blind Borromean Collective-Dynamics and Clock-Candidate Protocol v0.1.0

**Status:** proposed preregistration / NOT EXECUTED / NO PHYSICAL CLAIMS  
**Inputs:** user-provided `A006-v0.5.0.zip`; Guan, Zuccher & Liu (2025), *Physics of Fluids* 37, 024126, doi:10.1063/5.0252708.  
**Science policy:** no SST canonical constants, masses, time-dilation law, fitted clock frequency, or preferred topology weights in primary computation.

## 1. Source audit (read only)

The archive's active `CPFIXED61` group has 64 link geometries: two compositions (5_2,5_2,6_1 and 6_1,6_1,5_2) x four profiles (FLAT, SOFT, BALANCED, TIGHT) x four declared minimum-point classes (256,512,1024,2048) x original/mirror. **52/64** active link geometry records show `SHARP_TURN_WARNING`; **12/64** say `STATIC_CANDIDATE`. The release audit reports 168 active geometries, 336 prepared campaign cases, `runtime=NOT_EXECUTED`, `Milnor_triple=UNRESOLVED` and `Euler=NOT_RUN`. The analysis audit has `NO_KNOTPLOT_RUNTIME_DATA` and zero metric rows. The 32 stage generator reports cover compositions x profiles x resolutions, prior to original/mirror and closure-policy duplication. The archive also retains `CPCENTER` geometry controls. Do not confuse generation, KnotPlot pseudo-physical force relaxation, and fluid evolution.

In `SCIENCE_CONTRACT.md`, the six KnotPlot force-isolation arms alter bending, mechanical, and electrical force controls. They are **not** inviscid fluid forces. Root `run_all.cmd` does not presently expose `FORCEQUAL` dispatch even though `tools/force_qualification_v050b.py` exists; verify/install a separate versioned patch before relying on that interface. The current archive labels the collection `v0.5.0` but its release audit refers to `v0.5.0a` and contract `v0.5.0b`; record effective hashes rather than silently reconciling versions.

**Topology warning:** the 5_2 and 6_1 component knots are individually nontrivial; they are not the unknotted components of the canonical L6a4 Borromean rings. Near-zero pairwise Gauss linking numbers do **not** certify the full three-component link type. `Milnor_mu123` and component polynomial gates remain unresolved in A006.

## 2. Hypotheses, strictly separated

- **H0:** no numerical invariant, stable collective phase, or robust frequency survives qualification.
- **H1:** spontaneous geometrical oscillations arise from the source-native unforced dynamical equations.
- **H2:** three-component phase coupling is demonstrably different from single-component and two-component controls.
- **H3:** a robust internally observable oscillation remains periodic or quasi-periodic over the preregistered long horizon and under independent numerical refinement.
- **H4 (deferred):** a qualified mode may define a candidate operational clock. NO interpretation as physical proper time or SST time dilation without additional independent tests.

## 3. Blindness and source separation

1. Freeze original ZIP SHA-256 and every source geometry SHA-256. Never overwrite.
2. Generate arbitrary opaque `seed_id`s and two stores: `SEALED_SOURCE_MAP` (identity, composition, profile, resolution, handedness, closure policy) and `BLIND_INPUTS` (opaque ID, normalized coordinates, component boundaries, orientation/circulation metadata, independent raw hashes). Store independently; evaluator must not receive filename/class metadata.
3. Preregister `science_contract.json` and frozen gate algorithms, units, tolerances, holdout group assignments, output schema, and code revision before dynamic runs. Hold out at the **geometric family** level; mirror and discretized representations of one shape must stay together in the same partition.
4. Primary analysis is dimensionless and may use a fixed reference circulation magnitude `|Gamma_0|=1` *as a change of units* and explicitly varied sign sectors. No SST constants, preferred frequencies, force laws, or time-scaling parameters enter.
5. Conduct diagnostic development on a frozen development subset; keep holdouts inaccessible until algorithm and thresholds are locked. Never label a tuned development finding independent validation.
6. Only independent reviewers may reveal source identity after gate outputs and test metrics are signed and write-locked. Mark that reveal `REVEAL_ONLY`.

## 4. Model: no ad hoc feedback force

For smooth incompressible, inviscid, unforced Euler flow:

```latex
\partial_t\mathbf u +(\mathbf u\cdot\nabla)\mathbf u=-\rho^{-1}\nabla p,\quad \nabla\cdot\mathbf u=0,
\qquad
\partial_t\boldsymbol\omega=\nabla\times(\mathbf u\times\boldsymbol\omega).
```

Use the existing E010/PKLSA source-native finite-core Biot--Savart kernel only after an explicit 3-component extension is implemented and tested; the presently documented E010-v0.3.2 readiness qualifier accepts **single-component closed filaments only**. Treat this filament approximation as a separate model, not full Euler equivalence. Any reconnection in a smooth ideal Euler run must trigger numerical/model-review gates. Gross--Pitaevskii (GPE) reconnection is a **secondary benchmark** with different physics, not a required matching outcome.

Define one pre-frozen geometric scale `L_0` per normalized sample family, and:

```latex
 t^*=t|\Gamma_0|/L_0^2,\qquad \omega^*=\omega L_0^2/|\Gamma_0|.
```

Never compute a clock frequency by inserting a hypothesized proper-time law.

## 5. Observables

For component i with arclength `L_i(t)` and curvature `kappa_i(s,t)`, define a dimensionless shape signal:

```latex
Q_i(t)=\frac{L_0^2}{L_i(t)}\oint_{C_i(t)}\kappa_i(s,t)^2\,ds.
```

Additional independent outputs: `L_i/L_0`, normalized internal pairwise minimum distances, full geometry after rigid translation/rotation removal, signed circulations, total energy and impulse diagnostics, spatially resolved curvature signal, component topology, and collision/clearance diagnostics. In a core-resolved field model, only then add twist/helicity-based probes of possible torsional internal dynamics.

For causal feedback tests apply small, preregistered, balanced perturbations to **initial states only**, including no perturbation controls, and compute dimensionless response kernels:

```latex
R_{ij}(\tau)=\left.\frac{\partial Q_i(t^*+\tau)}{\partial\epsilon_j}\right|_{\epsilon=0}.
```

A three-cycle in the response matrix or coherent frequency locking is diagnostic of coupled dynamics; it does **not** by itself prove an irreducible three-body force. Use single, pair, triple, and geometry-matched unlinked control arms.

## 6. Gates

| Gate | Preregistered decision | Result prior to run |
|---|---|---|
| B0 | Raw hash/provenance, three closed components, no duplicated aliases | PENDING |
| B1 | Component knot types, pairwise linking, Milnor triple and full link classification | UNRESOLVED |
| B2 | Local finite-core resolution vs mesh, nearest-strand separation, short-horizon integrator convergence | NOT RUN |
| B3 | Invariants, numerical energy drift, finite-size/boundary sensitivity and no spurious reconnection | NOT RUN |
| B4 | Long-horizon geometry and robust bound/relative periodic orbit evidence | NOT RUN |
| B5 | Cross-response and independently measured causal loop/frequency with one/two/three-component controls | NOT RUN |
| B6 | Phase and frequency agreement across shape signals, analysis windows, temporal and spatial refinements | NOT RUN |
| B7 | Frozen holdout qualification, comparison of source families without post hoc tuning | NOT RUN |
| B8 | Independent full Euler and/or GPE external model comparison, explicitly separate interpretation | NOT RUN |
| B9 | `CLOCK_CANDIDATE` only if B0-B7 PASS; SST interpretation remains `UNRESOLVED` | NOT RUN |

Thresholds must be frozen using method verification and independent calibration controls **before** viewing any holdout dynamics. A persistent frequency with failed convergence remains `NUMERICAL_CANDIDATE`, not `CLOCK_CANDIDATE`.

## 7. First tranche / minimal scope

(A) static QA and normalizations across all 64 active `CPFIXED61` geometries; keep `CPCENTER` controls read-only; (B) test a single representative eligible shape from each profile/family plus matching single/two-loop controls, using **unforced** dynamics; (C) qualify finite-core resolution and temporal convergence before exploring signs, feedback, or long-horizon clock analysis; (D) freeze method, expand to holdouts, and only then compare with published GPE angle-series and SST interpretation.

**Do not treat KnotPlot's `bendforce`, `mechforce`, `elecforce`, or damping as physical Euler feedback.** A feedback mechanism should emerge from the off-diagonal dynamical response of the actual unforced solver. Any explicitly introduced stabilizer must be put in a visibly separate intervention arm and excluded from intrinsic-clock claims.

## 8. Expected artifacts

`SOURCE_FREEZE.json`, `SEALED_SOURCE_MAP.json` (separate access), `BLIND_INPUTS/`, `SCIENCE_CONTRACT.json`, `GATES.json`, `PRECHECK_AUDIT.csv`, `BLIND_RUN_RESULTS.jsonl`, `FEEDBACK_RESPONSE.csv`, `FREQUENCY_VALIDATION.csv`, `HOLDOUT_RESULTS.json`, `REVEAL.json`, and a final report labeling geometry, numerics, and physics separately. Preserve the existing A006 and E010 trees unchanged; use a sibling versioned experiment instance and `run_all.cmd` only after actual CLI semantics are verified.

## References

```latex
\bibitem{Guan2025}
H. Guan, S. Zuccher, and X. Liu (2025),
``Topological cascade of quantum Borromean rings,''
Physics of Fluids 37, 024126,
\url{https://doi.org/10.1063/5.0252708}.

\bibitem{Saffman1992}
P. G. Saffman (1992),
Vortex Dynamics, Cambridge University Press,
\url{https://doi.org/10.1017/CBO9780511624063}.

\bibitem{Pitaevskii1961}
L. P. Pitaevskii (1961),
``Vortex lines in an imperfect Bose gas,''
Soviet Physics JETP 13, 451--454,
\url{https://www.jetp.ras.ru/cgi-bin/e/index/e/13/2/p451?a=list}.
```
