# A006 v0.4.3b incremental — scientific contract

- `STATIC_CANDIDATE`; only static geometry construction and KnotPlot script generation are qualified by local tests.
- Original frozen A006 knot seeds and the v0.4.2d Borromean source modules are not edited.
- Whole-component Borromean placements are conditional candidates, not a proven `5_2 + 5_2 + 6_1` or `6_1 + 6_1 + 5_2` Borromean link.
- `LEGACY`, `CENTER`, and `MANUAL` placement policies are separate experiment protocols. A rigid rotation conserves component-intrinsic knot topology but does not automatically conserve the multicomponent link isotopy type.
- Genuine 3D mirroring changes chirality where applicable but no topological symmetry group follows solely from matching geometric scalars.
- `go beadlimit <integer>` is a KnotPlot capacity setting, not a physical model parameter.
- Runtime checkpoint data are `NOT_EXECUTED` until independently measured with KnotPlot on Windows. Do not promote results to Euler/PKLSA stability.
- Multicomponent XYZ must contain exactly 3 headerless numeric blocks, with exactly one blank line between blocks. `N` is per-component and may differ according to final placed arclength.
