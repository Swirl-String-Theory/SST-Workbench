# rodin_GUI3 v8

Adds an **Open update log** table window. Each Update can log:

- run summary: preset, drive, coil count, point count, current, bounds, grid, backend, cache status, B-field stats, null-voxel count
- lane summary: lane label, points, current multiplier, effective current, polyline length, bounding box

The table is compact by design. Full point-level data remains available via **Export coil CSV**.

Run:

```bash
pip install numpy matplotlib
python rodin_GUI3.py
```
