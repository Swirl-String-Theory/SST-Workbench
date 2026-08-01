# KnotPlot uniform-N300 runtime catalog

Runtime file: `knotplot_knots_data.js`  
SHA-256: `6cb8fddd5a8e006abf26462a158a58d2aed98dac04715679bb6fe2a81313a5d0`

The catalog contains Ridgerunner-polish candidates converted to uniform arc-length N300 XYZ centerlines and then to full-spectrum coefficients for compact transport. For VortexLab, the authoritative runtime geometry is the reconstructed **native N300 polygon**. Do not interpret the full-spectrum derivatives as an independent smooth/reach certificate.

| ID | family | status | components | L | max |Lk| |
|---|---|---:|---:|---:|---:|
| `knot_3.1` | classic-knot | near-ideal-candidate | 1 | 16.376343183 | 0 |
| `knot_4.1` | classic-knot | near-ideal-candidate | 1 | 22.426246813 | 0 |
| `knot_5.1` | classic-knot | relaxed-seed | 1 | 23.676233552 | 0 |
| `knot_5.2` | classic-knot | relaxed-seed | 1 | 25.979200834 | 0 |
| `knot_6.1` | classic-knot | relaxed-seed | 1 | 29.582629499 | 0 |
| `knot_7.1` | classic-knot | near-ideal-candidate | 1 | 30.705925579 | 0 |
| `link_6.3.1` | link | relaxed-seed | 3 | 35.805958031 | 1 |
| `link_6.3.2` | link | relaxed-seed | 3 | 39.435810687 | 0 |
| `link_6.3.3` | link | relaxed-seed | 3 | 29.046812109 | 1 |
| `torus_3.3` | torus-link | relaxed-seed | 3 | 25.645093715 | 1 |
| `torus_6.9` | torus-link | relaxed-seed | 3 | 109.581016552 | 6 |

`D=1` is source normalization/provenance. It does not by itself establish a physical SST core diameter, global ideality, or C2 reach of the uniform runtime centerline.

Legacy benchmark ID `Tlink_6_9` is migrated to `torus_6.9`. The latter carries explicit torus metadata p=6, q=9, three T(2,3) components, and expected pairwise linking magnitude 6.
