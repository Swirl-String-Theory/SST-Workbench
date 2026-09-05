# Input formats

Pass a directory (recommended) or ZIP containing relaxed closed centerlines. Recursive scan supports:

- KnotPlot/Ridgerunner `.vect`
- whitespace/comma/semicolon XYZ `.txt`, `.dat`, `.csv`
- `.npy` shaped `N x 3`
- `.npz` containing `points`, `xyz`, or `centerline`

Default search when no path is supplied:

1. `..\..\KnotPlot\knots\final`
2. `..\KnotPlot\knots\final`
3. `KnotPlot\knots\final`
4. `data\knots`

Do not pre-scale the files to metres. The workbench estimates rope thickness from the relaxed geometry, normalizes it to one, and only then maps one core radius to canonical `r_c` for physical output columns.
