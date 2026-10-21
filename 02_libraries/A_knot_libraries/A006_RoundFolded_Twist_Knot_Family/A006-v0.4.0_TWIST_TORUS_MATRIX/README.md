# RoundFolded NearUnknot v0.4.0 — Twist + Near-Circle Torus Knots

**DEVELOPMENT / STATIC_CANDIDATE — KnotPlot dynamics NOT EXECUTED in this release**

This is a versioned continuation of the previous RoundFolded NearUnknot v0.3.0 twist ladder. It adds the minimally-lobed `T(2,q)` torus family for odd q = 3,5,7,9,11, updates the 11-crossing labels, and replaces the previous log-spaced checkpoint campaign with hybrid early + linear 1000-step checkpoints.

## Names and mathematics

- Twist ladder `T_m=C(m,2)` m=1..9, topological names 3_1, 4_1, 5_2, 6_1, 7_2, 8_1, 9_2, 10_1, **K11a247** (11-crossing twist). For 3_1 the *primary campaign seed* is its thin `T(2,3)` torus embedding to meet the requested near-unknot morphology; the historical Fourier model remains preserved in src/build_ladder.py only as provenance.
- Torus `T(2,q)` with `q=3,5,7,9,11`: 3_1, 5_1, 7_1, 9_1, **K11a367**. Since 3_1 is both trefoil and torus, there are **13 unique knots** not 14.
- User aliases `11_1` (torus) and `11_2` (twist) are preserved only as explanatory historical labels, not used as ambiguous file IDs.

Near circular torus formula (KnotPlot arbitrary coordinates):

```
x=(R+a*cos(q*t))*cos(2*t)
y=(R+a*cos(q*t))*sin(2*t)
z=a*sin(q*t)
t in [0,2*pi),  R=78,  a=1.35,  q odd
```

It generates a genuine topological `T(2,q)` embedding for coprime (2,q), with relative envelope `a/R≈0.0173`. **The displayed cylinder radius `cradius=0.06` is visual only**, not a finite-core Euler vortex radius; nor does the geometry demonstrate toroidal rolling.

Existing twist source geometries use the v0.3.0 TikZ SmoothClasp / 4-plat branches and are copied as immutable KPT input assets, with ancestor reports, rather than silently regenerated from a different method. 11a247 matches the previously described v0.3.0 `11cross_T9` *intended family*, but distinct independent knot identity tests beyond Alexander are future work.

## Modes (two bead resolutions and TANF ON/OFF in each mode)

| Command | Knots | Max atomic iterations |
|---|---|---|
| `run_all.cmd BASIC` | 5_2, 6_1 | 8,000 |
| `run_all.cmd SMALL` | 3_1, 4_1, 5_2, 6_1 | 8,000 |
| `run_all.cmd MEDIUM` | 3_1, 4_1, 5_1, 5_2, 6_1, 7_1, 7_2, 8_1 | 16,000 |
| `run_all.cmd FULL` | all 13 unique twist and torus types up to 11 crossings | 32,000 |

Checkpoints per run: **0, 1, 8, 32, 128, 512, 1000, 2000, 3000, ...** up to the mode's horizon. The dense first six checkpoints detect immediate failure; every 1000 steps after 512 gives fixed-width panels and simple slope/variance analysis. `ago` rather than asynchronous `go` is mandatory.

**Important**: iterations are NOT physical time. Equal iteration counts across N1024 and N2048 are not matched Euler time steps. Increasing resolution does not automatically imply numerical stability or continuum convergence.

## On your Windows workstation

1. Unzip to a new versioned directory (never overwrite v0.3.0).
2. `py -3 -m pip install -r requirements.txt`
3. `run_all.cmd TEST` (checks all seeds, KPT roundtrips, target crossing structure, and script checkpoint arithmetic)
4. `run_all.cmd PREFLIGHT` (a real short `-stdin -nographics` KnotPlot test on your PC; should report `PREFLIGHT PASS`)
5. `run_all.cmd BASIC PLAN` (inspect `plans/BASIC.json` and scripts)
6. `run_all.cmd BASIC` — executes sequentially if KnotPlot executable was found and the preflight passed.
7. `run_all.cmd ANALYZE` — writes `analysis/matrix_long.csv`, `tanf_ab.csv`, `resolution.csv`, `coverage.csv`, audit JSON and real-result plots (once real data exist).

KnotPlot executable discovery: set environment variable `KNOTPLOT_EXE`, or put its absolute executable path into `config/knotplot_exe.txt`, or use default `%LOCALAPPDATA%\Programs\KnotPlot\KnotPlot.exe`. The original .lnk remains untouched. A shipped sample points to the original user's shortcut path, but is not an auto-update of the installed binary.

The program launches KnotPlot through the documented `-stdin -nographics` interface, sends a `read <script>` command, then processes the atomic checkpoint script. **The headless Windows CLI workflow is not tested in this environment.** If preflight fails, stop and run the generated `.kpc` scripts manually in the KnotPlot GUI; do not claim the campaign executed.

### Skip completed work

A run unit = one `(knot, bead N, tanforce arm, source KPT hash, solver parameter hash)` combination. `DONE.json` is written only by the orchestrator after a process exits successfully, all `.xyz` and `.k` checkpoints pass structural checks, and the final XYZ differs from the baseline.

A later mode **skips** that run unit if a completion of at least its required horizon exists with identical source and solver settings. Example: after BASIC 8k, SMALL skips completed 5_2 and 6_1 arms. MEDIUM 16k never resumes an 8k run from XYZ because the latter has no KnotPlot internal solver state; it restarts from baseline. Old outputs remain in their tier-specific folders. Missing/invalid checkpoints or changed input/configuration invalidate skipping.

Manual GUI runs are intentionally not automatically marked DONE, to avoid promoting incomplete/early asynchronous snapshots. Their `.xyz` can still be analyzed once runtime evidence is documented. On failure the orchestrator stops without promoting any physical claim.

## Saved outputs

- `output/seeds/<name>_N1024.{kpt,xyz}` and `_N2048.{kpt,xyz}` — 26 geometries.
- `scripts/<MODE>/<knot>_N<beads>_TANF_<ON/OFF>_<MODE>.kpc` — 108 KPC scripts.
- `runs/<knot>/N<beads>/<MODE>/TANF_<ON/OFF>/i<iteration>.xyz` and `.k`, plus runtime log and `DONE.json` after completion.
- `plans/*.json` — pending/skipped tasks, checksum-aware.
- `analysis/` — actual measurements only. Initial matrix contains **zero observed datapoints**, with missing cells clearly marked.

## Science contract

The new torus geometry was checked for expected planar crossings, alternating crossing assignments, Alexander polynomial, torus determinant, minimum discrete distance, and KPT/XYZ roundtrip. Twist sources retain existing geometric verification from v0.3.0. 

`KnotPlot relaxation ≠ inviscid Euler evolution`; no physical core radius, Biot–Savart self-induction, Floquet spectrum, local clock emergence, or toroidal roll is certified. Topology and crossing preservation **during long relaxations** still require independent per-checkpoint verification. The `safe` / `dowker` KnotPlot messages are diagnostics, not rigorous certificates.

## Sources

- KnotPlot command line options: https://knotplot.com/manual/CommandLineOptions.html
- KnotPlot command reference: https://knotplot.com/manual/commands.html
- Knot Atlas 11a247: https://www.katlas.org/wiki/K11a247
- Knot Atlas 11a367: https://katlas.org/wiki/K11a367