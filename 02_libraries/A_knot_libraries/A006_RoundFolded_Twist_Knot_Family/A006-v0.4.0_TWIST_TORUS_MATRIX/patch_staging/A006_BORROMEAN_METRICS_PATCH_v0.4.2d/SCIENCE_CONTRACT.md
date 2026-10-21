# Scientific contract — A006 Borromean v0.4.2d

1. Geometric source: near-unknot individual 5_2 and 6_1 curves from user's native v0.4.0 SEED_MANIFEST; references borromean_flat/balanced, whole-curve transport, no connected sum.
2. Intended composition 556 (5_2,5_2,6_1) or 665 (6_1,6_1,5_2) recorded per candidate.
3. Exactly three blocks of numeric x y z; precisely two empty separator lines; close cyclic polygon implicitly, never duplicate final point, no header/footer or alternate formats.
4. Equal arclength allocation using final placed lengths. Global scale changes physical/numerical separation relative to fixed KnotPlot `close` unless collision parameter is also adapted.
5. Static PASS: file shape, seam/edge distribution, approximate pairwise Gauss linking and segment clearance. Independent component knot invariants after deformation not yet independently verified. Milnor μ̄123 not implemented; Borromean status unresolved.
6. Dynamics/diagnostics: KnotPlot is a non-Euler artificial relaxation model. TANF ON carries a documented implementation defect, so ON/OFF are diagnostics only. Never interpret `ago` counts as physical times. Native data may include link-wide metrics, not per-component metrics.
7. Output in-place patch must never touch root run_all.cmd, knotplotrc, shortcuts, existing XYZs, or prior campaigns.
8. Correct results use literal `NOT_TESTED`, `UNRESOLVED`, or `NO_RUNTIME_DATA` instead of invented PASS.

References: R.G. Scharein, New KnotPlot Commands, 2017, https://knotplot.com/man/ ; R.G. Scharein, Interactive Topological Drawing, 1998, https://knotplot.com/thesis/thesis_a4.pdf.
