# KnotPlot_MultiTopology_QHP_Sweep_v0.3.2.3

Parameterized KnotPlot q/h/p sweep for knots, catalogue links and generated torus knots/links.

The package generalizes the trefoil balance campaign: instead of editing Python/KPC
files for every new topology or q/h/p range, the complete sweep is supplied on the
command line.




## v0.3.2.1 — fix for `0.2.1` / `0.3.1`

The `0.n.1` entries are explicit unlink/null controls. They no longer rely on
`load 0.n.1` plus a KnotPlot coordinate export to discover their components.

They are generated deterministically as separated equal-radius circles:

```text
0.2.1 -> 2 components -> 600 beads -> [300,300]
0.3.1 -> 3 components -> 900 beads -> [300,300,300]
0.4.1 -> 4 components -> 1200 beads -> [300,300,300,300]
```

This makes the null condition explicit and independent of catalogue/export behavior.

All nontrivial links still use KnotPlot itself for preparation and retain a strict
component-count check. A mismatch on a real link remains a hard failure rather
than silently changing topology.

If Stage 1 previously stopped during PREP at `0.2.1`, rerun the same command in
v0.3.2.1. No QHP relaxation had started at that point.



## v0.3.2.2 — robust real-link component extraction

A second Windows behavior showed that `coords` on a full catalogue link can flatten
component boundaries in the exported text. Therefore v0.3.2.2 no longer parses a
full-link `coords` file to discover components.

For every **real multi-component topology** the preparation script now does:

```text
reset all
load 2.2.1
keep 0
coords ...__comp000.txt

reset all
load 2.2.1
keep 1
coords ...__comp001.txt
```

For a 3-component link the topology is reloaded three times and components 0, 1 and 2
are exported independently.

KnotPlot's `keep component` command explicitly deletes all components except the
requested one, with components numbered starting at zero. Thus every exported prep
file must contain exactly one closed component.

Python then measures:

\[
L_0,L_1,\ldots,L_{n-1}
\]

and allocates:

\[
N_i\approx N_{\rm total}\frac{L_i}{\sum_j L_j}.
\]

This preserves the v0.3.1 length-proportional bead rule without relying on blank-line
separation from a full-link export.

`0.n.1` null controls remain synthetic explicit unlinks from v0.3.2.1.



## v0.3.2.3 — metric-neutral checkpoint resume

A resumed campaign previously did:

```text
load checkpoint.k
centre
fitto mindist 1.05
```

The `fitto` operation changes the metric scale, so a resumed trajectory could no
longer be compared continuously with its pre-interruption length / radius-of-gyration
history.

v0.3.2.3 resumes with:

```text
load checkpoint.k
mode cb
collision fast
energy model MD
restore frozen runtime parameters
restore q/h/p
ago ...
```

No `centre`, `refine`, or `fitto` is applied before resumed evolution.

Before any resumed `ago`, the runner launches a short probe that loads the checkpoint
with the same non-geometric settings and measures length and radius of gyration.
Continuation is allowed only when the reload agrees with the stored checkpoint within
a relative tolerance of `2e-5`.

Audits are stored in:

```text
campaigns/<name>/resume_checks/
```

Uninterrupted runs were not affected by the old bug.


# Live timer, ETA and progress logging

v0.3.2 no longer leaves the console apparently frozen while KnotPlot is calculating.

During every active KnotPlot run, the runner prints a heartbeat every 30 seconds by default:

```text
2026-08-25T21:14:30+02:00 [TIMER 0003/0300] KNOT_3p1__QHP_0002
elapsed=00:37:12 checkpoint=50000/100000 (50.0%)
runETA=00:35:10 campaignETA=6d 04:18:22 campaignElapsed=02:41:03
```

The same information is continuously appended to:

```text
campaigns/<name>/progress.log
```

Completed-run timing data is written to:

```text
campaigns/<name>/timings.csv
```

The ETA becomes more accurate as completed runs accumulate. The current-run ETA also
uses the latest completed KnotPlot checkpoint, so it can update during a single long
100k relaxation.

Change heartbeat frequency with:

```text
--progress-every=10
```

or:

```text
--progress-every=60
```

Every generated KPC also writes `CHECKPOINT` messages into its own KnotPlot log.

---

# Staged scientific campaigns

Four ready-to-run panels are supplied. All stage definitions are visible and editable in:

```text
stage_panels.json
```

The stage commands accept normal sweep overrides after the stage name.

## Stage 1 — highest scientific information

```bat
run_stage1.cmd
```

Contains the explicit null controls requested:

```text
0.1
0.2.1
0.3.1
```

plus the most discriminative topology comparisons:

```text
knots:
0.1, 3.1, 4.1, 5.1, 5.2, 8.19, 10.124

links:
0.2.1, 0.3.1, 2.2.1, 4.2.1, 5.2.1,
6.3.1, 6.3.2, 6.3.3
```

Default:

```text
--scripts=20
--max-ago=100000
```

This stage is intended to answer the highest-value questions first: null/unlinked
controls, simple linking, zero-linking-but-nontrivial links, Borromean higher-order
linking, chirality/family contrasts and torus-vs-non-torus knot structure.

## Stage 2 — torus knots / torus links

```bat
run_stage2.cmd
```

Catalogue controls:

```text
3.1, 5.1, 7.1, 9.1, 8.19, 10.124
```

Generated torus cases:

```text
2.3, 2.5, 2.7, 2.9,
3.4, 3.5,
3.3, 3.6, 3.9,
6.9, 6.15, 6.21
```

Default:

```text
--scripts=20
--max-ago=100000
```

This stage directly compares catalogue and analytic torus representations where possible.

## Stage 3 — twist knots

```bat
run_stage3.cmd
```

Frozen twist-knot ladder:

```text
3.1, 4.1, 5.2, 6.1, 7.2, 8.1, 9.2, 10.1
```

Default:

```text
--scripts=20
--max-ago=100000
```

## Stage 4 — rest / broad catalogue screen

```bat
run_stage4.cmd
```

This contains the remaining prime knots through 10 crossings, excluding the knots
already used in Stages 1–3, plus a broad residual low-crossing link panel.

Because this stage is much larger, its deliberate screening defaults are:

```text
--scripts=6
--max-ago=30000
```

Promising Stage-4 objects can then be rerun deeply with:

```bat
run_stage4.cmd --scripts=20 --max-ago=100000
```

Be aware that this is a very large campaign.

## Override any stage default

Examples:

```bat
run_stage1.cmd --scripts=10 --max-ago=50000
```

```bat
run_stage2.cmd --progress-every=10
```

```bat
run_stage4.cmd --scripts=3 --max-ago=10000
```

Run all four sequentially:

```bat
run_stages_all.cmd
```

For large campaigns it is usually more practical to run the stages individually.

---

# `--scripts=20`

In `--qhp-mode=line`, `--scripts` is the number of q/h/p configurations generated
**for every topology**.

Example:

```text
--scripts=20
--knots=3.1,5.1,7.1
```

means:

```text
3 topologies * 20 scripts = 60 KnotPlot relaxation runs
```

`--qhp-points` remains accepted as a backwards-compatible alias.

In `--qhp-mode=grid`, the number of scripts is instead determined by
`--qhp-steps=q_steps,h_steps,p_steps`.

---

# Length-proportional bead allocation for links

v0.3.1 no longer assumes that every component should receive the same number of beads.

`--beads-per-component=300` defines the **total budget scale**:

\[
N_{\rm total}=N_{\rm components}\times300.
\]

Before any q/h/p script is run, the package performs one KnotPlot geometry probe per
topology:

1. load/construct the untouched topology;
2. export its raw multi-component coordinates;
3. split components on the blank lines in KnotPlot's coordinate format;
4. measure the closed arclength \(L_i\) of every component;
5. allocate the total bead budget proportionally;
6. uniformly resample each component on its own arclength;
7. write one frozen `prepared_inputs/<topology>.txt`;
8. all q/h/p scripts for that topology load this exact prepared input.

The target allocation is:

\[
N_i \simeq N_{\rm total}\frac{L_i}{\sum_j L_j},
\qquad
\sum_iN_i=N_{\rm total}.
\]

Integer rounding uses a deterministic largest-remainder allocation.

## Example: `7.2.1`

`7.2.1` is a two-component catalogue link, so with:

```text
--beads-per-component=300
```

the total budget is:

```text
2 * 300 = 600 beads
```

If the measured component lengths are:

```text
component 0: L = 1
component 1: L = 2
```

then the allocation is:

```text
component 0 -> 200 beads
component 1 -> 400 beads
total       -> 600 beads
```

This is based on **measured component arclength**, not component index or equal splitting.

Every topology receives an audit file such as:

```text
campaigns/<name>/prepared_inputs/LINK_7p2p1.allocation.json
```

containing:

```text
component_lengths
length_fractions
allocated_beads
allocated_fractions
allocation_sum
```

The generated prepared coordinate file preserves components using blank-line separation.

A ready example is:

```bat
run_example_link_7p2p1_100k.cmd
```

You can enforce a minimum resolution per component:

```text
--min-beads-per-component=12
```

The minimum acts only as a safety floor. If the pure proportional allocation already exceeds it, the exact length ratio is preserved.

---

## Install

```bat
run_00_install.cmd
```

The package expects the normal repository layout:

```text
SST-Workbench/
└─ KnotPlot/
   ├─ KnotPlot.lnk
   └─ KnotPlot_MultiTopology_QHP_Sweep_v0.3.0/
```

You can override the shortcut:

```bat
set KNOTPLOT_LNK=C:\path\to\KnotPlot.lnk
```

---

# Main syntax

```bat
run_sweep.cmd ^
  --qhp-min=q_min,h_min,p_min ^
  --qhp-max=q_max,h_max,p_max ^
  --qhp-mode=line ^
  --scripts=20 ^
  --max-ago=100000 ^
  --knots=3.1,5.1,7.1 ^
  --links=6.3.3,6.3.1 ^
  --torus=3.3,3.6,3.9,6.9,6.15,6.21
```

`--knots`, `--links`, and `--torus` can be used independently or together.

## Your requested multi-topology example

For the balance region identified around the trefoil, a sensible starting range is:

```bat
run_sweep.cmd ^
  --qhp-min=42.0586,1.43298,6.215 ^
  --qhp-max=44.3970,1.47040,6.320 ^
  --qhp-mode=line ^
  --scripts=20 ^
  --max-ago=100000 ^
  --knots=3.1,5.1,7.1 ^
  --links=6.3.3,6.3.1 ^
  --torus=3.3,3.6,3.9,6.9,6.15,6.21 ^
  --beads-per-component=300 ^
  --name=MultiTopology_qhp_100k
```

This means:

```text
3 catalogue knots
2 catalogue links
6 torus objects
-----------------
11 topologies

20 q/h/p scripts per topology
----------------------------
220 KnotPlot runs
```

There is also a ready command:

```bat
run_example_multitopology_100k.cmd
```

## What does `--qhp-min` / `--qhp-max` mean?

### Recommended: `--qhp-mode=line`

With:

```text
--qhp-min=42,1.43,6.20
--qhp-max=44,1.47,6.32
--scripts=20
```

the package produces 20 points along the joint q/h/p line:

\[
(q_i,h_i,p_i)
=
(q_{\min},h_{\min},p_{\min})
+
\alpha_i
[(q_{\max},h_{\max},p_{\max})-(q_{\min},h_{\min},p_{\min})].
\]

This is the direct generalization of the q/h/p balance-ray experiments.

A broad input such as:

```text
--qhp-min=1,1,1 --qhp-max=10,10,10
```

is syntactically valid, but it is an extremely broad physics scan. For the current
balance question, the `42..44 / 1.43..1.47 / 6.21..6.32` range above is far more useful.

### Full 3D grid

To vary q, h and p independently:

```bat
run_sweep.cmd ^
  --qhp-min=40,1.3,6.0 ^
  --qhp-max=46,1.6,6.5 ^
  --qhp-mode=grid ^
  --qhp-steps=5,5,5 ^
  --max-ago=30000 ^
  --knots=3.1
```

This makes:

```text
5 * 5 * 5 = 125 q/h/p states
```

per topology.

Be careful: a `10,10,10` grid is 1000 states **per topology**.

The package has a default `--max-runs=5000` guard against accidental campaign explosion.

---

# Topology syntax

## Catalogue knots

```text
--knots=3.1,5.1,7.1
```

becomes:

```text
load 3.1
load 5.1
load 7.1
```

## Catalogue links

KnotPlot names a multi-component catalogue link as `C.k.n`, where `k` is the number
of components. Therefore:

```text
--links=6.3.3,6.3.1
```

becomes:

```text
load 6.3.3
load 6.3.1
```

Both examples have 3 components.

## Torus objects

The CLI notation:

```text
--torus=3.3,3.6,3.9,6.9,6.15,6.21
```

is translated as:

```text
torus 3 3 ...
torus 3 6 ...
torus 3 9 ...
torus 6 9 ...
torus 6 15 ...
torus 6 21 ...
```

If `gcd(p,q)>1`, KnotPlot creates a torus link.

---

# Bead count

Default:

```text
--beads-per-component=300
```

This defines the total budget from component count, but **does not force equal
beads per component**. The final distribution is proportional to measured component
arclength.

Examples of total budgets:

```text
knot 3.1       -> 1 component -> 300 total beads
link 7.2.1     -> 2 components -> 600 total beads, length-proportional
link 6.3.3     -> 3 components -> 900 total beads, length-proportional
torus 6.9      -> 3 components -> 900 total beads, length-proportional
```

To force the same total bead count everywhere:

```text
--total-beads=600
```

---

# Long runs and `--max-ago`

Example:

```text
--max-ago=100000
```

does not mean one blind `ago 100000`.

The package inserts automatic checkpoints, including dense early measurements and
progressively later checkpoints up to the requested maximum.

For a 100k campaign the schedule contains early points such as:

```text
0, 10, 25, 50, 100, 250, 500, 1000, 2000, 4000, 6000, 8000, 10000
```

plus long-time checkpoints generated from the final horizon.

To specify them yourself:

```text
--checkpoints=0,100,1000,5000,10000,25000,50000,75000,100000
```

Every checkpoint stores:

```text
*.metrics.csv
*.k
```

The metrics include KnotPlot's:

```text
iteration
length
radius of gyration
nbeads
safeness
```

The final coordinates are stored by default.

Use:

```text
--save-coords=all
```

to write coordinates at every checkpoint, or:

```text
--save-coords=none
```

to suppress them.

---

# Resume after interruption

Long campaigns are checkpoint-resumable.

If, for example, a 100k run stopped after the 60k checkpoint, running the exact same
command again detects the saved `.k` state and continues from 60k.

Do **not** use `--force` unless you explicitly want to restart every selected run.

---

# Plan without running

Before a large campaign:

```bat
run_plan.cmd ^
  --qhp-min=42.0586,1.43298,6.215 ^
  --qhp-max=44.3970,1.47040,6.320 ^
  --scripts=20 ^
  --max-ago=100000 ^
  --knots=3.1,5.1,7.1 ^
  --links=6.3.3,6.3.1 ^
  --torus=3.3,3.6,3.9,6.9,6.15,6.21
```

It prints the exact run count, component count and bead count without creating/running
the campaign.

Generate KPCs but do not execute:

```text
--generate-only
```

---

# Analysis

Each completed campaign gets:

```text
campaigns/<name>/analysis/REPORT.md
campaigns/<name>/analysis/REPORT.json
campaigns/<name>/analysis/runs.csv
```

For each topology the analyzer reports:

- best measured q/h/p state by late `E`;
- late expansion/contraction response;
- late drift;
- direct near-equilibrium candidates;
- adjacent expansion/contract sign crossings in `line` mode;
- safeness diagnostics.

The balance observable remains:

\[
E(i)=\frac12\left[
\frac{L(i)-L_0}{L_0}
+
\frac{R_g(i)-R_{g0}}{R_{g0}}
\right].
\]

A geometric zero is still a balance surrogate, not by itself proof of restoring
stability or TBK/RPO stability.

---

# Useful examples

Trefoil only, 100k:

```bat
run_example_k31_100k.cmd
```

All requested topologies, 100k:

```bat
run_example_multitopology_100k.cmd
```

Pack a completed campaign:

```bat
run_pack_campaign.cmd MultiTopology_qhp_100k
```

Full help:

```bat
.venv\Scripts\python.exe sweep.py --help
```
