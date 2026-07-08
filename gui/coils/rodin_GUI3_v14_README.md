# rodin_GUI3 v14 layout/grid build

Fixes/changes:

- Bundle is physically created and verified.
- Default field backend is now `SSTcore C++ fast`.
- Auto-bounds margin is doubled from 1.45 to 2.90 so the field grid/quiver reaches about 2x farther.
- Added `Show 3D grid` checkbox.
- `Quad views` renders as a real 2x2 grid:
  - Perspective | Top
  - Front       | Side
- Heatmaps render underneath the 3D views in a vertical split.
- If `Heatmap plane = All 3 planes`, bottom row shows XY z=0, XZ y=0, YZ x=0.

Run:

```bash
pip install numpy matplotlib
python rodin_GUI3.py
```

Optional speed backend:

```bash
pip install SSTcore
python rodin_GUI3.py
```
