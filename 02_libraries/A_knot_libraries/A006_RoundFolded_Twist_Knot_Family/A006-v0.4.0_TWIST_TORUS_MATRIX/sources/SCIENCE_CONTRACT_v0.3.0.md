# v0.3.0 Scientific Contract

\(T_m\) means the twist-knot family with m half-twists, 1≤m≤9.
Do not call m=9 `11_2` as a standard knot-table ID until a KnotInfo crosswalk is obtained.
The expected Alexander polynomials (ascending coefficients; up to ±t^k) are
odd m=2k-1: [k, -(2k-1), k], even m=2k: [k, -(2k+1), k].
The determinant is \(|Δ(-1)|=2m+1\).
The implementation checks the actual 3D exported polygon as well as combinatorics.

Knot shape is not fully parameterized by topology: two branches are used
(TikZ-derived and generalized 4-plat). Their matching morphologies are an
explicitly OPEN geometry design question.

Research design: TANF on/off 9×2×2 arms, PILOT to 512 and gated FULL to 32,000.
Nine checkpoints per full arm. Pairwise A/B matched at same seed and N; across N
compare normalized geometries and convergence, not 'physical time'.

Only real KnotPlot output can validate trajectory behavior; no fake metrics.
