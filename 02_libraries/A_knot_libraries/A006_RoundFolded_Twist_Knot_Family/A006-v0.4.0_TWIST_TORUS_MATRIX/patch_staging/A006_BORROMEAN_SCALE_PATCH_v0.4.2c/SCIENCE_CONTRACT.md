# Science Contract — A006 v0.4.2c

- Input objects: THREE whole, previously generated near-unknot curves 5_2, 5_2, 6_1 from A006-v0.4.0, transported against flat or balanced user-provided Borromean reference carriers.
- No local knot insertion, splicing, or unreported geometric reattachment.
- Scale applies uniformly to **all three coordinate axes of all three curves**. This conserves dimensionless shape ratios, but does not change renderer radii or numerical force/contact parameters in KnotPlot.
- Nmin allocation: N_i = round(Nmin * L_i / min_j L_j), where L_i are **transported, pre-resample** closed polygon lengths. All lengths in internal KnotPlot geometry units.
- Closed periodic sample: includes last-to-first edge, no repeated closing vertex; a 50-phase deterministic arclength grid search maximizes minimum sampled chord-to-median ratio without modifying the source polygon connectivity.
- Fail if closure edge ratio outside [0.65,1.35], other edge ratios outside [0.55,1.35], any static self/intercomponent separation <=0.20, or coarse pairwise Gauss integrals outside ±0.02.
- Never write partial rejected XYZ. All valid geometry exported as a **single headerless XYZ** with exactly one blank line between each of three components.
- `STATIC_CANDIDATE` means the stated static numerical tests passed. It **does not certify** that the transported 3D components have types 5_2/5_2/6_1, that the Milnor triple-linking invariant is nonzero, or that the assembly is dynamically stable.
- KnotPlot `close` / component flags, GUI display radii, and `ago` require independent local execution.
- The source native length ratio (6_1)/(5_2) ≈1.13775 is NOT used for bead allocation here; placed lengths are different.
