# Ruban (E010) catalog converter for VortexLab

This package contains:

- `ruben_knot_data.js` — Fourier catalog from E010 Ruban Torus Dynamics Family XYZ seeds (filename spelling **ruben_***; scientific labels **Ruban (E010)**).
- `build_ruben_knot_data.py` — converter for those `.xyz` exports.

Deployed to:

```text
05_apps/A003_vortexlab/apps/web/data/ruben_knot_data.js
```

loaded from `apps/web/index.html` as `./data/ruben_knot_data.js`.

## Current catalog

| Source | Count | ID pattern |
|--------|------:|------------|
| `seeds/T_p_q/*.xyz` | 84 | `RUBEN_T_{p}_{q}_B####_N512` |
| `seeds_perturbed/.../*_eps01.xyz` | 84 | `RUBEN_T_{p}_{q}_B####_N512_eps01` |

**Total: 168 entries.** Native **N=512**, single filament (knots only). Pretty-print size typically ~10–15 MB.

UI defaults: variant **baseline**, embedding/B0 **All** (or first available). Filters: embedding (`T_2_3`…), B0 (0.08–0.20), variant (baseline/perturbed).

Canonical copies:

```text
05_apps/A003_vortexlab/vortexring-lab/ruben_knot_data.js
05_apps/A003_vortexlab/apps/web/data/ruben_knot_data.js
```

## Source geometry

```text
01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/
  E010_Ruban_Torus_Dynamics_Family_v0.3.5-outputs/
    FAMILY_INDEX.json
    seeds/
    seeds_perturbed/
```

Embeddings: `T_2_3`, `T_2_5`, `T_2_7`, `T_3_2`, `T_3_4`, `T_3_5`, `T_3_7`, `T_4_3`, `T_4_5`, `T_5_2`, `T_5_3`, `T_5_4`.  
B0 grid: 0.08, 0.10, …, 0.20. Topology IDs from `FAMILY_INDEX` where known (`3_1`, `5_1`, …); some embeddings have `topology=null`.

## Generate / refresh

From `05_apps/A003_vortexlab/tools/catalog`:

```powershell
python .\build_ruben_knot_data.py `
  --output ..\..\vortexring-lab\ruben_knot_data.js

Copy-Item ..\..\vortexring-lab\ruben_knot_data.js ..\..\apps\web\data\ruben_knot_data.js -Force
```

Expect **168** entries. Optional minify: `--compact`.

## Entry schema (KnotPlot/Twist-like)

- `sourceRole`: `e010-ruban-baseline-N512` or `e010-ruban-perturbed-N512`
- filter fields: `kind`, `topology`, `parametricEmbedding`, `B0`, `variant`, `resolutionN`
- `family`: `ruban-torus`
- `torus`: `{p,q,notation,B0,parametricEmbedding}`
- `ideal: false`, `D: null`

## Scientific status

Entries are E010 static/candidate geometries (status `INITIAL_GEOMETRY_ONLY_DYNAMICS_NOT_RUN` in the source pack) converted to discrete Fourier series for VortexLab sampling. They are **not** certified as global ideal/tight, ropelength-minimizing, or dynamics/survival results.

## Tests

```powershell
python -m unittest tests.test_build_ruben_knot_data -v
```
