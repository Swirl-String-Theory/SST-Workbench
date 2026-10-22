# Force Qualification Science Contract — v0.5.0b

- **Qualification question:** Is the sharp clasp/turn concentration dominated by (i) inadequate bending coefficient, (ii) mech-only contraction or (iii) elec-only repulsion?
- **Not a source-change experiment:** All six arms load the SAME exact three-component headerless, empty-line-separated v0.5.0a seed; record its SHA-256 and initial component bead counts. No new link geometry is generated.
- **Independent variations:** bend 0/1/10/100 while mech+elec ON; then mech-only and elec-only with bending OFF. All other script parameter lines identical.
- **Primary measurements:** per-component maximum discrete turning angle (degrees), 99th-percentile turning angle, discrete curvature (inverse KnotPlot coordinate), max-curvature index, minimum/median/maximum edge, length, and closure edge uniformity, all computed from XYZ.
- **Gate Q0:** all six initial geometries identical. The code checks parsed floating coordinates, not textual KnotPlot headers.
- **Gate Q1:** 0/1/8/32/128 checkpoints, native CSV 5 records, unchanged bead counts and component order. Missing data → INCOMPLETE, no inferred pass.
- **Gate Q2:** verify requested `collision fast` via observed `collision` console response, plus `safe` messages. Must be separately recorded by the operator. DO NOT certify topology from a screenshot of only the setting.
- **Gate Q3:** evaluate bend parameter sensitivity. A single lower curvature peak is diagnostic, not proof of stability; check all three components and entire trajectory.
- **Gate Q4:** inspect geometry for self-intersections/reconnections and compare independent invariants before topology PASS. Pairwise linking ≈ 0 is insufficient to establish a Borromean link.
- **Gate Q5:** no Euler, finite-core Biot–Savart, or Swirl-String Theory physical interpretation may be inferred from KnotPlot pseudo-physical relaxation alone.
- **Known instrumentation:** native `/s` is unsupported in the installed KnotPlot build, and native `/l`, `/g` are multicomponent-sensitive; only `/I,/N,/l,/g` is used for diagnostic CSV.
- **Safety:** `BEND_100`/`MECH_ONLY` might produce rapid pinching; early checkpoint inspection before long-duration runs advised. The script includes `collision` and `safe` readback to console but cannot autonomously stop based on their printed content in an interactive GUI.
