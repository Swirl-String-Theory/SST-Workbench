# A006 v0.4.2b Science Contract

**Construction**: three complete 5_2,5_2,6_1 near-unknot seed centerlines, transported as a whole around the original FLAT/BALANCED references. This is not the classical componentwise local-knot connected-sum construction.

**Testable static predicates**: (i) strict three-block numeric-only XYZ, (ii) N0,N1,N2 correctly counted, (iii) periodized reference interpolation, (iv) last-to-first edge approximately matches all other edges, (v) collision-clearance >0.20 KnotPlot coordinate units at current geometry scale, (vi) numerical pairwise Gauss linking approx 0.

**Unknown**: full embedding isotopy of each component under transport; Milnor triple invariant; potentially even Borromean topology; closed component flag after ASCII import; dynamic invariants; Euler/PKLSA self-induced movement. None of those may be inferred from static output. `length in short direction = 5.654867` is an independent printed statistic and not a bead-spacing calibration.

**Falsification**: component knot polynomial != expected, nonzero pairwise linking, absent nontrivial triple invariant, contact or self-intersection, failing after-KnotPlot closure, loss of intended component topology after a single atomic relax step.

**Limit of repair**: The patch targets large polygonal jumps caused by angular interpolation at 0/2pi; periodic resampling removes remaining discretization irregularities without independently certifying topological isotopy. No smoothing that might cross strands is applied.
