# Historical reference conclusions on bundled `3_1` inputs

These are **reference recomputations**, not hard-coded expected answers. Use the history runners to reproduce them from the immutable archived code.

## v0.1.0 BASIC

Overall: `FAIL`.

Both sources returned the same gate pattern:

```text
G0 PASS
G1 PASS
G2 FAIL
G3 FAIL
G4 PASS
G5 FAIL
G6 PASS
```

Key values:

| Source | normalized growth | cross growth improvement | nearest cross-lobe pair rate | cross Jacobian fraction |
|---|---:|---:|---:|---:|
| Fremlin fseries | 0.8880253693 | -0.4319405312 | +0.1169939025 | 0.9811847000 |
| KnotPlot final | 0.7978293089 | -0.5350206526 | +0.02564257594 | 0.8162246190 |

Interpretation: the nearest cross-lobe pair is locally separating in both representations, but the reduced six-mode dynamics is unstable and removing cross-lobe coupling reduces the worst growth rate rather than increasing it.

## v0.1.1 BASIC

Overall: `FAIL`, numerically identical to the v0.1.0 scientific result on these inputs. v0.1.1 primarily corrected Windows packaging/build behavior.

## v0.2.0 BASIC reference validation

Overall: `FAIL`; the original critical pattern remains:

```text
G0 PASS
G1 PASS
G2 FAIL
G3 FAIL
G4 PASS
G5 FAIL
G6 PASS
```

New diagnostics on the full BASIC settings show:

- `G7` FAIL for both: curvature-matched scrambles do not show a seed stability advantage.
- `G8` FAIL for both at the preregistered coherence threshold: the closest pair separates, but the sign is not sufficiently coherent across all selected close contacts/lobe-centroid pairs.
- `G9` FAIL for both: the cross-lobe contribution to the most unstable eigenmode has **positive** real part, i.e. it is destabilizing for that mode in this reduced model.
- `G10` FAIL for both: the dominant eigenvector has substantial `m=0` participation but the `m=0/E` block leakage is too large for a clean single-sector description.
- `G11` PASS for both: short full-versus-without-cross nonlinear counterfactual evolution orders growth in the same direction as the linear modal attribution.

Selected v0.2.0 BASIC values:

| Source | close-contact separating fraction | lobe-pair separating fraction | dominant cross contribution / spectral scale | C3 block leakage |
|---|---:|---:|---:|---:|
| Fremlin fseries | 0.5833333333 | 0.3333333333 | +0.1703235605 | 0.8596646652 |
| KnotPlot final | 0.5833333333 | 0.6666666667 | +0.3811221354 | 0.7788399834 |

This sharpens the v0.1 conclusion: **local cross-lobe separation exists, but it is not equivalent to global self-confinement.** In the resolved dominant reduced eigenmode, cross-lobe coupling is instead a positive growth contribution for both source geometries.

## v0.3.0 BASIC reference validation

Overall: `FAIL`. The immutable legacy critical pattern remains unchanged for both source representations:

```text
G0 PASS
G1 PASS
G2 FAIL
G3 FAIL
G4 PASS
G5 FAIL
G6 PASS
```

The v0.2 diagnostics also reproduce the same qualitative interpretation: the nearest cross-lobe contact separates, while cross-lobe coupling does not stabilize the dominant six-mode instability.

### New coupled TBK diagnostics

Both datasets resolve a mixed oscillatory breathing/torsion/Kelvin mode with good finite-difference convergence, so `G12` passes. The new family-coupling ablations, however, do **not** support a stabilizing TBK balance at BASIC resolution:

| Source | coupled Jacobian convergence | minimum B/T/K participation in selected oscillatory mode | torsion decouple penalty | Kelvin decouple penalty | breathing decouple penalty | all-family block-diagonal penalty |
|---|---:|---:|---:|---:|---:|---:|
| Fremlin fseries | 0.01496490017 | 0.07840437569 | -0.09013686986 | -0.1578467597 | -0.0007407520 | -0.1578467597 |
| KnotPlot final | 0.02182863955 | 0.06427550070 | -0.1158361571 | -0.1223571358 | -0.02691696924 | -0.1223571358 |

The growth penalty convention is

\[
\Delta g_f=
\frac{g(J_{\rm decouple\,f})-g(J)}{\rho(J)}.
\]

Thus the negative values mean that, in this resolved expanded linear model, **decoupling the family reduces the worst growth rate**. The tested torsion/Kelvin/inter-family couplings therefore act destabilizing rather than providing the hypothesized balancing stabilization around these particular seeds.

The expanded full normalized growth is approximately `0.3279` (Fremlin) and `0.3282` (KnotPlot). Strong Kelvin participation is present in several oscillatory eigenmodes, but presence of Kelvin-like motion is not by itself evidence of stabilization.

### Guarded RPO/Floquet result

All four BASIC phase trials for both sources reached the required shape excursion, but their best later recurrence occurred at the current peak rather than after a genuine return. The measured return ratio was therefore approximately

\[
R(T)/R_{\rm peak}=1,
\]

which fails the preregistered `rpo_return_ratio_max = 0.65` criterion.

Consequently:

```text
G17_TBK_phase_lock  FAIL / not activated by a valid RPO
G18_RPO_recurrence  FAIL
G19_Floquet_bounded FAIL / Floquet intentionally not interpreted
```

This is an important negative result: v0.3.0 does **not** convert a slowly drifting near-start trajectory into an artificial periodic-orbit claim. An RPO/Floquet interpretation requires a genuine excursion followed by a geometric return.

### v0.3 BASIC diagnostic pattern

For both sources:

```text
G12 PASS   mixed TBK oscillatory mode resolved and converged
G13 FAIL   torsion coupling not stabilizing by ablation
G14 FAIL   Kelvin coupling not stabilizing by ablation
G15 FAIL   breathing coupling not stabilizing by ablation
G16 FAIL   collective inter-family coupling not stabilizing
G17 FAIL   no valid RPO-conditioned TBK phase lock
G18 FAIL   no excursion-and-return RPO
G19 FAIL   no valid RPO-conditioned Floquet verdict
```

This does not rule out a nonlinear periodic balance elsewhere in state space. It falsifies the narrower BASIC hypothesis that the two tested relaxed `3_1` seeds already sit close enough to such a TBK-stabilized orbit for the preregistered expanded-mode/RPO diagnostics to resolve it.
