# Third-party boundary

This archive does not vendor KnotPlot, Ridgerunner, pyknotid, Spherogram, SnapPy, KnotTheory`, or the Shadertoy shader source.

It contains only independent SST code plus a minimal factual KAtlas reference snapshot with source URLs.

Optional integrations detected at runtime:

- pyknotid — MIT (external package)
- Spherogram — GPLv2+ (external package)
- SnapPy — GPLv2+ (external package)
- KnotPlot — external/proprietary application; no redistribution
- Ridgerunner/plCurve — external tool/data source; no redistribution here

The mathematical constructions inspired by the supplied shaders were reimplemented independently; shader rendering/SDF source code is not included.

## Format references used without redistribution

- Ridgerunner uses plCurve; plCurve documents its on-disk curve format as human-readable Geomview VECT.
- v0.2.4 independently implements the documented VECT grammar, including `#` comment handling; no plCurve
  or Ridgerunner source code is copied into this archive.
