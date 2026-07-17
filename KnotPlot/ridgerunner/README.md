# Ridgerunner (portable, next to knotplotrc.kps)

This folder is a self-contained Windows bundle for tightening KnotPlot XYZ
`.txt` centerlines with ridgerunner.

## One-time setup

```powershell
cd <this-folder>
powershell -ExecutionPolicy Bypass -File .\install-user-path.ps1
```

Needs Python 3 on PATH for `.txt` runs.

## Help

```bat
ridgerunner --help
```

Shows **wrapper** options (checkpoints, `--label`, `--verbose`, `--full-output`, …).
For native ridgerunner flags (`-c`, `--EqForceOn`, `--StopResidual`, …):

```bat
bin\ridgerunner.exe -h
```

## Usage

```bat
ridgerunner -a -s 1000 C:\pad\naar\knotplot.txt
```

- **New seed:** `-a` (autoscale to thickness 0.501).
- **Continue** from a previous RR XYZ output: `-c` (no rescaling).

During a `.txt` run the wrapper shows an ASCII progress bar. Use `--verbose`
for classic per-step `Rop:` lines.

Checkpoint tag comes from `-s` / `--StopSteps`:

| `-s` | tag | main outputs next to the input |
|------|-----|--------------------------------|
| 1000 | `001k` | `knotplot_rr_001k.txt`, `.metrics.json`, `.vect`, `.rr\` |
| 5000 | `005k` | `knotplot_rr_005k.txt`, … |
| 10000 | `010k` | `knotplot_rr_010k.txt`, … |
| 20 | `s20` | `knotplot_rr_s20.txt`, … |

Optional `--label NAME` appends `_{NAME}` so parallel runs do not overwrite:

```bat
ridgerunner -c -s 10000 --label plain prev_rr_005k.txt
→ prev_rr_005k_rr_010k_plain.txt
```

### Equilateralization

| Flag | When it matters |
|------|-----------------|
| `--EqOn` | Occasional eq when max/min edge **> 3** |
| `--EqForceOn` | Continuous equilateralization force (can interfere with stepper) |

### Recommended workflow (3-stage pipeline)

Do **not** start with a single huge `--EqForceOn` run on a fresh KnotPlot
seed. Prefer:

1. **coarse** — new seed, pure tightening (`--EqOn` only as emergency edge fix)
2. **eqfinal** — restore vertex spacing with `--EqForceOn`, drive residual to 0.01
3. **polish** — short unbiased run without continuous EqForce

Primary seed is chosen by the checkpoint gate (not blindly 5k/10k/15k).

```bat
rem Stage 1
ridgerunner -a --EqOn -s 10000 --StopResidual=0.05 --label coarse "seed.txt"

rem Stage 2
ridgerunner -c --EqForceOn -s 50000 --StopResidual=0.01 --Stop20=0.000001 --label eqfinal "seed_rr_010k_coarse.txt"

rem Stage 3
ridgerunner -c --EqOn -s 20000 --StopResidual=0.01 --Stop20=0.0000001 --label polish "…_eqfinal.txt"
```

Or: `ridgerunner\run_three_stage.cmd path\to\seed.txt`

The **polish** output is the near-ideal candidate; keep eqfinal as checkpoint.

### KnotPlot build + seed gate (`run_build.cmd`)

```bat
cd C:\workspace\projects\SST-Workbench\KnotPlot

rem KnotPlot only: 15k checkpoints, log + *.knotplot.json sidecars
run_build.cmd torus_6.9

rem Auto-select one trial seed, then 3-stage ridgerunner
run_build.cmd torus_6.9 -rr

rem Overrides
run_build.cmd knot_3.1 -rr --seed trial_009k
run_build.cmd knot_3.1 -rr --multistart
run_build.cmd knot_4.1 -rr --allow-unverified-topology
```

`-rr` does **not** pipeline every TXT. It runs `select_knotplot_seed.py`
(after `parse_knotplot_log.py`) and sends **one** seed to `run_three_stage.cmd`.
After polish, stage 4 writes a **separate** VortexLab copy via
`resample_closed_knot_txt.py --points 300` → `*_polish_uniform_N300.txt`
(+ VECT). The Ridgerunner `*_polish.txt` is left untouched; do not re-run
Ridgerunner on the uniform file.

**Robuuste checkpoint-gate (summary):**

- Plateau on **`R_proxy = L/D_proxy`** deltas (`|ΔR/R| < 0.001` after the local min) → status `settled-after-local-minimum`; earliest 0.1%-tie only among candidates at/after that min. No plateau → pure min `R_proxy` (`best-so-far-no-plateau`); **no** earliest-tie without settle. Same path for `knot_*` / `torus_*` / `link_*`.
- Signed length gain is logged for diagnostics only (KnotPlot length often grows).
- Per-component flatness `√(λ3/λ1)`; 5% drop = soft penalty; ~20–25% + worse `D_proxy`/`R_proxy` = hard DQ
- `D_proxy = min(2·MinRad, d_self_nonlocal, d_inter)` from **segment–segment** distances (arc-length exclusion window)
- Rank by class A/B/C then lowest `R_proxy`
- Topology (`knot_*` / `torus_*` / `link_*`): 1-comp prefers **`knot_type`** from folder (`knot_X.Y` / `torus_p.q`); `link_*` prefers **`link_type`** from folder (then `linking_matrix`). If the primary field is missing, consistent non-empty **`dowker_code`** across checkpoints verifies. Hard fail if both are absent.
- No settle by 15k → `best-so-far-no-plateau` warning, still may RR

Check `*.metrics.json` after eqfinal/polish: residual ≤ 0.01, prefer
`edge_length_ratio` ≤ 1.10 and `edge_length_cv` ≤ 0.01.

### Quick single checkpoints (trefoil)

```bat
ridgerunner -a -s 1000 C:\workspace\projects\SST-Workbench\KnotPlot\knots\knot_3.1\T_2_3_trial_005k.txt
ridgerunner -a -s 5000 C:\workspace\projects\SST-Workbench\KnotPlot\knots\knot_3.1\T_2_3_trial_005k.txt
```

### Metrics

Each checkpoint writes JSON with length, thickness, ropelength, residual,
**strutcount** (contact struts, from `.final.struts` / `strutcount.dat` col 2 — not MRstruts),
edge_length_variance, **edge_length_min/max/ratio/mean/cv** (from
final XYZ), **mr_struts** (separate), flatness, component sizes, and paths.

### Multilink without blank-line separators

```bat
ridgerunner -a -s 1000 --component-count 3 link_900verts.txt
ridgerunner -a -s 1000 --component-size 300 link_900verts.txt
```

### Full ridgerunner file output

```bat
ridgerunner --full-output -a -s 1000 knot.txt
```

(`--keep-vectfiles` is a deprecated alias for `--full-output`.)

Plain VECT files still go straight to the native exe (no checkpoint renaming):

```bat
ridgerunner -a -s 1000 knot.vect
```

## Layout

| Path | Role |
|------|------|
| `ridgerunner.cmd` | Entry point (put this folder on PATH) |
| `run_three_stage.cmd` | coarse → eqfinal → polish for one seed TXT |
| `select_knotplot_seed.py` | checkpoint gate → one trial seed |
| `parse_knotplot_log.py` | KnotPlot log → `*.knotplot.json` sidecars |
| `run_knotplot_txt.py` | txt → VECT → ridgerunner → `{stem}_rr_{tag}[_{label}].*` |
| `bin\ridgerunner.exe` | Native binary + MinGW DLLs |
| `bin\*.dll` | OpenBLAS / GSL / runtime deps |

Do not place `ridgerunner.cmd` inside `bin\` next to the `.exe` — Windows
prefers `.exe` over `.cmd` in the same directory.