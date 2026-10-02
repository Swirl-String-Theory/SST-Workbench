# Provider matrix

| Provider/source | Bundled? | Main role | Can certify XYZ topology? | Notes |
|---|---:|---|---:|---|
| SST internal core | yes | geometry, frames, writhe/linking, gates | no | does not infer knot identity |
| KAtlas snapshot | yes, minimal factual records | reference PD/Gauss/DT/braid/invariants | no | byte-hashed offline snapshot |
| pyknotid | no | identify/analyse space curves | yes | optional MIT dependency |
| Spherogram | no | planar diagram / link calculations | not directly from XYZ in this adapter | GPLv2+; independent reference cross-check |
| SnapPy | no | hyperbolic complement geometry | no XYZ identity in this adapter | GPLv2+; useful for hyperbolic volume cross-check |
| KnotPlot | no | geometry generation/relaxation/exported topology data | externally | proprietary/external; never redistributed |
| Ridgerunner/plCurve | no | constrained ropelength relaxation | no | external; VECT/XYZ outputs are importable |
| `ideal.txt` | data | embedding | no | source family, not a topology oracle |
| `fseries` | data | embedding/series source | no | only explicit XYZ form auto-loaded |

The library intentionally avoids making one provider authoritative for all tasks.
