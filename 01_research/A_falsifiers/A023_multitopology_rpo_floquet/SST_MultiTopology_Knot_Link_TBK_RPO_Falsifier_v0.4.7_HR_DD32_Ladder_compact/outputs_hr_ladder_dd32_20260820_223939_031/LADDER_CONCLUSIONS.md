# SST v0.4.7 High-Resolution DD32 Convergence Ladder

Datasets analyzed: **127**.

- CONVERGED_PASS: **2**
- CONVERGED_FAIL: **5**
- UNRESOLVED: **120**
- INCOMPLETE: **0**

## Decision discipline

- Spatial convergence uses R0/R1/R2: N=360/540/720 at fixed k_max=8.
- Spectral convergence uses R2/R3/R4: k_max=8/12/16 at fixed N=720.
- A power-tail extrapolation is diagnostic only and is accepted only when the measured tail is quasi-monotone, contracting, and verdict-stable.
- R5 keeps the reference Jacobian at eps=0.004. eps=0.012/0.016 are separate finite-amplitude robustness probes and do not enter P1.
- Large weight on the k_max=16 basis boundary marks spectral truncation unresolved.
- DD32 is not IEEE FP64; the generated confirmation queue identifies cases requiring CPU/OpenMP FP64 audit.

## Most threshold-sensitive / unresolved

| source | class | final g | spatial | spectral | kmax weight | eps J drift | FP64 reasons |
|---|---|---:|---|---|---:|---:|---|
| knotplot:knot_3.1 | UNRESOLVED | 0.1179615 | False | False | 6.497e-05 | 0.1896 | resolution_or_threshold_unresolved, near_growth_threshold |
| knotplot:torus_2.3 | UNRESOLVED | 0.1233611 | False | False | 8.463e-09 | 0.2286 | resolution_or_threshold_unresolved, near_growth_threshold |
| fremlin:6_1:knot.6_1 | UNRESOLVED | 0.1243239 | False | False | 0.03455 | 0.08447 | resolution_or_threshold_unresolved, near_growth_threshold |
| knotplot:knot_8.1 | UNRESOLVED | 0.1150349 | False | False | 0.04043 | 0.2351 | resolution_or_threshold_unresolved, near_growth_threshold |
| knotplot:link_0.3.1 | UNRESOLVED | 0.1278135 | True | False | 7.459e-10 | 0.1661 | resolution_or_threshold_unresolved, near_growth_threshold |
| knotplot:knot_8.17 | UNRESOLVED | 0.1119292 | False | False | 0.1096 | 0.2687 | resolution_or_threshold_unresolved, near_growth_threshold, large_epsilon_J_drift |
| fremlin:8_2:knot.8_2 | UNRESOLVED | 0.1297942 | True | False | 0.1023 | 0.2288 | resolution_or_threshold_unresolved, near_growth_threshold |
| knotplot:knot_9.2 | UNRESOLVED | 0.1301111 | True | False | 0.02213 | 0.2466 | resolution_or_threshold_unresolved, near_growth_threshold |
| knotplot:link_6.2.1 | UNRESOLVED | 0.1318285 | True | False | 0.001694 | 0.2097 | resolution_or_threshold_unresolved, near_growth_threshold |
| knotplot:torus_3.9 | UNRESOLVED | 0.1325786 | False | False | 0.006248 | 0.4779 | resolution_or_threshold_unresolved, near_growth_threshold, large_epsilon_J_drift |
| knotplot:link_0.2.1 | UNRESOLVED | 0.1061597 | True | False | 9.737e-10 | 0.08448 | resolution_or_threshold_unresolved, near_growth_threshold |
| fremlin:7_2:knot.7_2 | UNRESOLVED | 0.1060452 | True | False | 1.504e-27 | 0.2071 | resolution_or_threshold_unresolved, near_growth_threshold |
| knotplot:knot_10.1 | UNRESOLVED | 0.1002182 | True | False | 0.01351 | 0.2765 | resolution_or_threshold_unresolved, near_growth_threshold, large_epsilon_J_drift |
| knotplot:torus_2.6 | UNRESOLVED | 0.1444929 | True | False | 9.719e-08 | 0.1819 | resolution_or_threshold_unresolved |
| fremlin:6_2:knot.6_2 | UNRESOLVED | 0.09449003 | True | False | 0.02073 | 0.123 | resolution_or_threshold_unresolved |
| knotplot:knot_6.2 | UNRESOLVED | 0.08944173 | False | False | 0.01865 | 0.2357 | resolution_or_threshold_unresolved |
| knotplot:torus_2.4 | UNRESOLVED | 0.08908322 | True | False | 0.004017 | 0.231 | resolution_or_threshold_unresolved |
| knotplot:knot_10.123 | UNRESOLVED | 0.1517024 | False | False | 0.09177 | 0.2839 | resolution_or_threshold_unresolved, large_epsilon_J_drift |
| knotplot:knot_8.18 | UNRESOLVED | 0.1525329 | True | False | 0.1544 | 0.3054 | resolution_or_threshold_unresolved, large_epsilon_J_drift, dominant_mode_hits_kmax_boundary |
| knotplot:torus_3.6 | UNRESOLVED | 0.1541977 | False | False | 0.001365 | 0.3878 | resolution_or_threshold_unresolved, large_epsilon_J_drift |
| knotplot:knot_9.35 | UNRESOLVED | 0.08495378 | False | False | 0.0268 | 0.2533 | resolution_or_threshold_unresolved, large_epsilon_J_drift |
| knotplot:knot_5.1 | UNRESOLVED | 0.1555222 | False | False | 0.03245 | 0.1074 | resolution_or_threshold_unresolved |
| fremlin:3_1:knot.3_1 | UNRESOLVED | 0.1598391 | True | False | 2.209e-27 | 0.045 | resolution_or_threshold_unresolved |
| fremlin:9_2:knot.9_2n | UNRESOLVED | 0.07929092 | True | False | 0.0384 | 0.2756 | resolution_or_threshold_unresolved, large_epsilon_J_drift |
| knotplot:knot_7.1 | UNRESOLVED | 0.1659974 | True | False | 0.005293 | 0.1331 | resolution_or_threshold_unresolved |
| fremlin:8_7:knot.8_7s | UNRESOLVED | 0.1684311 | True | False | 0.0635 | 0.1254 | resolution_or_threshold_unresolved |
| knotplot:knot_6.1 | UNRESOLVED | 0.06992541 | True | False | 0.05407 | 0.1909 | resolution_or_threshold_unresolved |
| knotplot:knot_4.1 | UNRESOLVED | 0.06840528 | False | False | 0.0258 | 0.1985 | resolution_or_threshold_unresolved |
| fremlin:3_1:knot.3_1p | UNRESOLVED | 0.1717713 | True | False | 2.406e-26 | 0.03461 | resolution_or_threshold_unresolved |
| fremlin:10_1:knot.10_1n | UNRESOLVED | 0.06523352 | True | False | 0.05913 | 0.2642 | resolution_or_threshold_unresolved, large_epsilon_J_drift |
| knotplot:link_7.2.8 | UNRESOLVED | 0.06482052 | True | False | 0.01481 | 0.3826 | resolution_or_threshold_unresolved, large_epsilon_J_drift |
| knotplot:knot_6.3 | UNRESOLVED | 0.06195658 | False | False | 0.03652 | 0.2683 | resolution_or_threshold_unresolved, large_epsilon_J_drift |
| knotplot:torus_3.3 | UNRESOLVED | 0.06136212 | True | False | 0.0003584 | 0.4387 | resolution_or_threshold_unresolved, large_epsilon_J_drift |
| knotplot:link_6.3.1 | UNRESOLVED | 0.0600473 | False | False | 0.001258 | 0.4736 | resolution_or_threshold_unresolved, large_epsilon_J_drift |
| knotplot:knot_7.3 | UNRESOLVED | 0.05938118 | True | False | 0.09962 | 0.2443 | resolution_or_threshold_unresolved |
| fremlin:5_2:knot.5_2 | UNRESOLVED | 0.05919274 | True | False | 0.01233 | 0.08837 | resolution_or_threshold_unresolved |
| fremlin:7_5:knot.7_5 | UNRESOLVED | 0.1808648 | True | False | 0.02374 | 0.1136 | resolution_or_threshold_unresolved |
| fremlin:7_3:knot.7_3 | UNRESOLVED | 0.1829641 | False | False | 0.003956 | 0.0811 | resolution_or_threshold_unresolved |
| knotplot:torus_2.8 | UNRESOLVED | 0.184356 | True | False | 0.003967 | 0.1629 | resolution_or_threshold_unresolved |
| knotplot:link_7.2.5 | UNRESOLVED | 0.05546777 | True | False | 0.01733 | 0.4273 | resolution_or_threshold_unresolved, large_epsilon_J_drift |
