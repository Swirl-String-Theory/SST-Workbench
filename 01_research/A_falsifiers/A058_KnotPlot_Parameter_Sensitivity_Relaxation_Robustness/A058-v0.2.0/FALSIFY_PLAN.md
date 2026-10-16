# Falsify plan — A058 v0.2.0

1. Keep one topology only: catalogue trefoil 3.1, fixed at 300 beads.
2. Leave all non-strength relaxation controls at reset-all defaults.
3. Sample each strength magnitude with a quarter-octave ladder: m=2^(k/4), k=-16..16, plus m=0.
4. Active-default axes share one global m=1 condition. The reset-all-disabled third axis is conditionally enabled and gets its own m=1 reference. Total = 101 conditions.
5. Save XYZ at 0, 250, 1000, 4000, 10000, 15000 relaxation iterations; do not depend on KnotPlot `data` CSV logging.
6. Analyze D_shape, L/Rg, edge-CV, reciprocal asymmetry, local quarter-octave robustness, zero-equivalence and diagnostic quadratic fits in x=log2(m).
7. Certify coordinate scalar metrics with C++17/pybind11 FP64.
8. Preserve Framework-v1.0.6 G4/G6/G7 semantics; do not repurpose disabled lanes.
9. Reveal strength-axis semantics only after commitment verification.
