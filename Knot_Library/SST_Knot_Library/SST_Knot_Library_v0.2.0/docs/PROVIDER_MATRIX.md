# Provider matrix

## Topology / geometry tools (executables & libs)

| Provider/source | Bundled? | Main role | Can certify XYZ topology? | Notes |
|---|---:|---|---:|---|
| SST internal core | yes | geometry, frames, writhe/linking, gates | no | does not infer knot identity |
| KAtlas snapshot | yes, minimal factual records | reference PD/Gauss/DT/braid/invariants | no | byte-hashed offline snapshot |
| pyknotid | no | identify/analyse space curves | yes | optional MIT dependency |
| Spherogram | no | planar diagram / link calculations | not directly from XYZ in this adapter | GPLv2+; independent reference cross-check |
| SnapPy | no | hyperbolic complement geometry | no XYZ identity in this adapter | GPLv2+; useful for hyperbolic volume cross-check |
| KnotPlot **exe** | no | geometry generation/relaxation | externally | proprietary/external; never redistributed; PATH discovery only |
| Ridgerunner **exe** | no | constrained ropelength relaxation | no | external; VECT/XYZ outputs are importable |

## Data providers (`Knot_Library/Sources` — provenance IDs)

| Human directory | `provider_id` | Construction objective | Notes |
|---|---|---|---|
| `Ideal_Gilbert` | `gilbert_ideal` | SONO → near-ideal rope → Fourier | Also Fourier; not the same as Fremlin |
| `FourierSeries_Fremlin` | `fremlin_fourier` | Elegant/symmetric 3D + Fourier/coords | Separate provenance from Gilbert |
| `KnotPlot_Scharein` | `knotplot` | KnotPlot-authored embeddings | Classes: original / seed / relaxed / export; exe ≠ data class |
| `Ridgerunner_Cantarella_Rawdon` | `ridgerunner` | Ropelength / near-ideal polylines | Distinct from KnotPlot database |
| `KAtlas_BarNatan` | `katlas` | Topology/reference | Braid **data** ≠ SST braid **realization** |
| `SST_Generated` | `sst_generated` | Analytic / braid / shader constructions | Never mix into Gilbert/Fremlin/RR |

`ideal.txt` / `fseries` filenames are embedding formats, not topology oracles and not provider IDs.

The library intentionally avoids making one provider authoritative for all tasks.
Software never parses directory names for identity — only `SOURCE.json` / `providers.json`.
