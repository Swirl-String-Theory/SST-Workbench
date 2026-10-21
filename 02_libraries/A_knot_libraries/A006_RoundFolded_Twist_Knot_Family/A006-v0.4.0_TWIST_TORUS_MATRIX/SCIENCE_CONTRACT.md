# Scientific qualification and gate definitions — v0.4.0

## Intended topology

| Family | IDs | Geometry | Verified | Unresolved |
|---|---|---|---|---|
| Twist | 4_1, 5_2, 6_1, 7_2, 8_1, 9_2, 10_1, K11a247 | Reused v0.3.0 static seed XYZ/KPT | Existing crossing counts / Alexander polynomial, source checksum, clearance | Full independent knot identity (e.g. Jones), evolution topology |
| Torus | T(2,3/5/7/9/11) | Exact smooth analytic embedding sampled at 1024/2048 | Projection crossings, alternating over/under, Alexander, determinant, KPT roundtrip, clearance | KnotPlot stability, physical torus rolling |

**Case 3_1:** canonical campaign geometry is torus formula (same knot type as trefoil), not the original 2015 Fourier sample. Source changes vs v0.3.0 are explicit.

## Numerical protocol

- Fixed KnotPlot parameters, compared to the previous v0.3.0 protocol: `close=0.20`, `max-dr=0.02`, `collision fast`, `energy model MD`, damped force model, `mechforce=on`, `elecforce=on`, `tanforce={on,off}`, `tanmag=9`; no geometric `fitto` rescale.
- Atomic `ago` between checkpoints; programmatic `coords` after each atomic segment; separate run from baseline for each arm and mode.
- Analysis does NOT equate iteration index with absolute time and does not infer a physical velocity.
- Discrete minimum segment distances do not certify that a continuous swept path has avoided all reconnections during the run.
- Scripts may be long; full mode is potentially very expensive (52 arms × 32000 = 1,664,000 KnotPlot iterations, including independent repetitions across tiers).

## Gates

G0: finite, closed, correctly sized component. G1: projected crossing pattern and polynomial. G2: KPT/XYZ equality. G3: minimum nonlocal distance + nonuniform-bead check. G4: one-step Windows headless KnotPlot `ago` smoke. G5: complete and nonidentical snapshots. G6: TANF arm independence. G7: resolution comparison. G8: topological invariants and segment clearance at every captured checkpoint. G9: independent Biot–Savart/Euler numerical validation. G10: self-induced toroidal rotation/translation physical prediction.

v0.4.0 BUILD qualifies G0–G3 for the static inputs. G4–G10 remain unresolved until real workstation execution. G8 needs stronger knot-type identification and checks on swept segments; G9–G10 cannot be passed by KnotPlot relaxations alone.

## Interpretation safeguards

- A visually circular embedding can still be nontrivially knotted; a global ring-like outline is not a `0_1` isotope.
- The projected central winding of a 2-pass toroidal filament is not the circulation, which remains an independently prescribed vortex property.
- Thin visual tube radius and `R/a` geometric ratio are not an SST core-radius prediction.
- A family-wide statistic pooling different knot morphologies is NOT evidence of a universal particle-mass or gravity law.
