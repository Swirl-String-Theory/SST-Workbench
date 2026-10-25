from pathlib import Path
import json,shutil,hashlib,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'MANIFEST.json').read_text());out=root/'KPS'
expected={'4_1':(4,5),'7_2':(7,11),'8_1':(8,13),'9_2':(9,15),'10_1':(10,17),'11a247':(11,19)}
for lab in expected:
 for n in (1024,2048):
  for profile in ['ROUND','TIKZ_NATIVE']:
   name=f'KNOT_{lab}_N{n:04d}_ORIG_{profile}'
   txt=f'''% New source-derived TikZ Hobby embedding; no Euler or relaxation.
% Start KnotPlot with CWD set to this package root.
reset all
mode cb
draw normal
load SEEDS/{name}.kpt
close all
information
display
'''
   (out/(name+'.kps')).write_text(txt,encoding='utf8')

fig=plt.figure(figsize=(16,9),layout='constrained')
for i,lab in enumerate(expected):
 name=f'KNOT_{lab}_N1024_ORIG_ROUND.xyz'
 p=np.loadtxt(root/'SEEDS'/name)
 ax=fig.add_subplot(2,3,i+1,projection='3d')
 ax.plot(p[:,0],p[:,1],p[:,2],lw=1.7)
 ax.plot([p[-1,0],p[0,0]],[p[-1,1],p[0,1]],[p[-1,2],p[0,2]],lw=1.7)
 ax.set_title(lab)
 m=p.mean(axis=0);radius=max(np.ptp(p,axis=0))/2;ax.set_xlim(m[0]-radius,m[0]+radius);ax.set_ylim(m[1]-radius,m[1]+radius);ax.set_zlim(m[2]-radius,m[2]+radius)
 ax.view_init(elev=48,azim=55);ax.set_axis_off()
fig.suptitle('A006 v0.5.0f | Roundfolded XYZ models regenerated from TikZ Hobby (N1024)')
fig.savefig(root/'PREVIEWS'/'SIX_3D_CANDIDATES.png',dpi=175)
plt.close(fig)

# Audit summary convenience CSV.
audit=json.loads((root/'REPORTS'/'INDEPENDENT_AUDIT.json').read_text())['results']
with (root/'REPORTS'/'PASS_AUDIT.csv').open('w',newline='',encoding='utf8') as f:
 wr=csv.DictWriter(f,fieldnames=['filename','label','crossing_count','determinant','alexander','min_abs_crossing_z','actual_3d_lift_ok','KPT_roundtrip_exact','full_audit_pass']);wr.writeheader()
 for r in audit:
  wr.writerow({k:r.get(k) for k in wr.fieldnames})

readme=r'''# A006-v0.5.0f — Reconstruction from NEW TikZ Hobby source diagrams

**Status:** `GEOMETRY_STATIC_CANDIDATE / KNOTPLOT_RUNTIME_NOT_TESTED / EULER_NOT_RUN`.

## Why this version exists

The earlier v0.5.0d angular-gap narrowing **did not repair the visual gap** seen in KnotPlot. The v0.5.0e diagnostic confirmed that a KPT component being flagged as "closed" does *not* demonstrate the intended overall 3D geometry. The six affected seed families are completely regenerated using the eight `*.tex` files supplied on 23 October 2026, rather than transformed from earlier 4-plat annular sources.

## Input and reconstruction

- The eight original `.tex` source files are preserved unchanged in `REF_TIKZ/`.
- `pdflatex` compiles an isolated **closed Hobby shortcut path** from each original coordinate list, and `pdftocairo -svg` exposes exact cubic Bezier control geometry produced by TikZ. **This is not a plain `CubicSpline` replacement for Hobby.**
- The planar curve is sampled as a continuous periodic curve. Actual planar crossings are detected from the source shape, and a smooth periodic height lift assigns alternating over/under encounters. This is **an independent 3D alternating embedding**, *not* an assertion that crossing enumeration agrees with the TikZ `flip crossing/.list` indexing; that correspondence remains unverified.
- Two profiles: `TIKZ_NATIVE` (source outline) and `ROUND` (positive-radius radial squeeze, alpha=0.65). Both are resampled on 3D arclength at N256, N512, N1024, N2048. Original and mirror are separate.
- `KPT` stores `Attr=1` (closed), and all filenames represent one periodic component, without a duplicate final bead.

## File dispositions

| Family | Native + ROUND, N256/512/1024/2048, ORIG/MIRROR | Role |
| --- | ---: | --- |
| `4_1`, `7_2`, `8_1`, `9_2`, `10_1`, `11a247` | 96 | Intended replacement families |
| `6_1` | 16 | Control only; not for installation |
| `5_2` | 0 new geometry | Known-good original left untouched; user's source P3=P10 yields 8 rather than 5 geometric intersections |
| `3_1` | 0 new geometry | Known-good original left untouched |

Of the 96 replacement cases, **84 passed all geometric gates** and reside in `SEEDS/`. **12** `ROUND N256` cases failed the maximum local turning-angle gate and reside in `QUARANTINE/`. The source-derived `6_1` control has 16 cases under `CONTROL_NOT_FOR_INSTALL/` and is never installed.

## Numerical validation (source and exports)

| Knot | Plane intersections | Alexander polynomial Δ(t), up to ±t^k | det(K)=|Δ(-1)| |
|---|---:|---|---:|
| `4_1` | 4 | 1 − 3t + t² | 5 |
| `7_2` | 7 | 3 − 5t + 3t² | 11 |
| `8_1` | 8 | 3 − 7t + 3t² | 13 |
| `9_2` | 9 | 4 − 7t + 4t² | 15 |
| `10_1` | 10 | 4 − 9t + 4t² | 17 |
| `11a247` | 11 | 5 − 9t + 5t² | 19 |
| `6_1` (control) | 6 | 2 − 5t + 2t² | 9 |

`REPORTS/INDEPENDENT_AUDIT.json` verifies **all 112 exports**, including quarantined and control files: projected crossing count; Fox-coloring determinant; Alexander polynomial (N512+); **actual signed Z-order at every projected crossing**; and exact KPT float64 roundtrip. 112/112 pass this audit. Quarantined files remain excluded because their curvature/turning-angle gate fails; passing topology is insufficient for geometry qualification. Segment distance excludes a local neighbor band and **is not an independently calculated vortex core thickness**.

## KnotPlot smoke test (NO relaxation)

Extract this ZIP preserving the directory layout. Start KnotPlot with its current working directory set to the extracted package root. Then run:

```
read KPS/KNOT_8_1_N1024_ORIG_ROUND.kps
```

Or:

```
reset all
load SEEDS/KNOT_8_1_N1024_ORIG_ROUND.kpt
close all
information
display
```

The first step is visual inspection **without any `go` or relaxation**. If the same visually missing upper arc remains, export the in-program KnotPlot coordinates and compare against `SEEDS/*.xyz`. A console message `Component #0 is closed` is only a component metadata check; it is not a morphology certificate. Do **not** overwrite the v0.5.0d or historical files before the KnotPlot visual comparison is successful.

## Safe integration

`install_sidecar.py` installs only to `<A006-base>/tikz_hobby_v050f/`, refuses collisions, and **never replaces** the existing gallery inputs, original_frozen, tests, registry, or physics runs. The gallery must be retargeted separately **after successful visual smoke test**. It intentionally does not add or remove gallery metadata.

```
python install_sidecar.py --target "C:\\workspace\\projects\\SST-Workbench\\02_libraries\\A_knot_libraries\\A006_RoundFolded_Twist_Knot_Family\\A006-v0.5.0" --dry-run
python install_sidecar.py --target "C:\\workspace\\projects\\SST-Workbench\\02_libraries\\A_knot_libraries\\A006_RoundFolded_Twist_Knot_Family\\A006-v0.5.0" --apply
```

## Reproduction

```
python -m pip install numpy scipy shapely sympy matplotlib
python src/rebuild.py
python src/prepare_release.py
python src/independent_audit.py
python src/package_release.py
```

Also requires a working LaTeX system (`pdflatex`, TikZ Hobby library) and `pdftocairo` executable. SHA-256 hashes for source inputs, output XYZ and KPT files are in `MANIFEST.json`.

## Limits

- No direct KnotPlot runtime test was performed in this environment.
- No exact reproducibility of the original TikZ `flip crossing/.list` *sequence* is claimed; an independently alternating spatial lift was used and its Alexander and determinant invariants were checked.
- `11a247` retains its legacy label; the Alexander polynomial and determinant are not by themselves a complete independent classification as the named standard knot.
- Static segment clearance does **not** establish a permissible vortex-core radius, topological isotopy during relaxation, Kelvin mode stability, Biot–Savart dynamics, or incompressible Euler (Euler equations) solutions.

## Literature

```latex
\bibitem{Alexander1928} J.~W. Alexander (1928), ``Topological Invariants of Knots and Links,'' Transactions of the American Mathematical Society 30, 275--306. \url{https://doi.org/10.1090/S0002-9947-1928-1501429-1}.
```
'''
(root/'README_NL.md').write_text(readme,encoding='utf8')

installer=r'''#!/usr/bin/env python3
"""Non-destructive A006 v0.5.0f installer; never overwrites existing gallery files."""
import argparse, shutil, sys
from pathlib import Path

src=Path(__file__).resolve().parent
ap=argparse.ArgumentParser()
ap.add_argument('--target',required=True,help='Existing A006-v0.5.0 base directory')
grp=ap.add_mutually_exclusive_group()
grp.add_argument('--dry-run',action='store_true')
grp.add_argument('--apply',action='store_true')
ns=ap.parse_args()
target=Path(ns.target).resolve()
if not target.is_dir(): sys.exit(f'ERROR: existing target folder not found: {target}')
dest=target/'tikz_hobby_v050f'
if dest.exists():sys.exit(f'BLOCKED: sidecar already exists; refusing overwrite: {dest}')
if target==src or src in target.parents:sys.exit('BLOCKED: cannot install to package root')
print(f'Source: {src}\nTarget: {dest}\nNon-destructive sidecar only (existing seeds remain unchanged)')
if not ns.apply:
 print('DRY RUN ONLY: no changes made. Add --apply to copy sidecar.');sys.exit(0)
try:
 shutil.copytree(src,dest,ignore=shutil.ignore_patterns('_tex_build','__pycache__','*.pdf','*.svg','*.log','*.aux'))
except Exception:
 shutil.rmtree(dest,ignore_errors=True)
 raise
print('CREATED:',dest)
'''
(root/'install_sidecar.py').write_text(installer,encoding='utf8')
print('Prepared package:',len(list((root/'KPS').glob('*.kps'))),'KPS and preview')
