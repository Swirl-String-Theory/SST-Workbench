# A006 — Volume–Circulation–Core Radius Closure v0.1.0 (VCCR)

**Status: ANALYTICAL / HYPOTHESIS-DEPENDENT / NOT PHYSICAL CERTIFICATION.**  This is a new, isolated research sidecar. It never modifies A006 seeds, `knotplotrc.kps`, `run_all.cmd`, ForceGrid scripts, or existing results.

## What it actually does

- Implements an analytically exact **uniform circular material tube** closure with fixed volume `V` and circulation `Gamma`.
- Computes the reference numerical SST trefoil calibration and stretch table in **SI units**.
- Reads native A006 **ASCII** `XYZ`, including three blank-line-delimited Borromean components, with component-local length, bead spacing, and turning angles in **original coordinate units**.
- Computes conditional **per-component physical radius ratios along a snapshot trajectory** when the operator asserts the same material tubes and coordinate scale; no bead-by-bead material tags needed for global length comparisons.
- Optionally compares two datasets with the **same material-segment correspondence**; derives individual segment radii and cross-sectional average vorticity from segment-length ratios.
- Computes **conditional** knotted-tube upper radius / minimum length bounds **only from an externally supplied ropelength bound**. There is no built-in claim that any particular A006 seed is a tight ideal knot.
- Produces JSON/CSV reports with explicit `PASS`, `UNRESOLVED`, and `NOT_RUN` gates.

## Quick start (standalone)

Install NumPy once: `py -3 -m pip install -r requirements.txt`.

```bat
run_vccr.cmd TEST
run_vccr.cmd DEMO
run_vccr.cmd analytic --stretch 1 1.5 2 4 --out Output\VCCR_v0.1.0
run_vccr.cmd geometry examples\KNOT_5_2_N0512_ORIG.xyz examples\KNOT_6_1_N0512_ORIG.xyz
run_vccr.cmd geometry examples\LINK_5_5_6_BALANCED_N0512_ORIG_CPFIXED61.xyz
run_vccr.cmd trajectory path\frame0.xyz path\frame128.xyz --assert-same-material-tube --out Output\VCCR_v0.1.0
run_vccr.cmd saturated --R-d 16.3714672385 20 30 --out Output\VCCR_v0.1.0
run_vccr.cmd bounds --Rmin-d 16.3714672385 --out Output\VCCR_v0.1.0
```

**Warning:** `saturated` is a *thought experiment*, not an inference from the XYZ geometry: it assumes the physical vortex core fills a geometrically embedded circular tube. In `bounds`, use a **qualified independent minimum** ropelength, not a random `L/d` of an unrelaxed embedding; numerical minima may be approximate bounds.

## Install inside the existing A006-v0.5.0 folder (sidecar, no patch stacking)

Copy/extract this package anywhere; from its package directory:

```bat
py -3 install_sidecar.py --base "C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0" --check
py -3 install_sidecar.py --base "C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A006_RoundFolded_Twist_Knot_Family\A006-v0.5.0" --apply
```

Then from the A006 root run `run_vccr.cmd TEST` or `run_vccr.cmd DEMO`. This adds only `tools/VCCR_v0.1.0/**` and a new top-level `run_vccr.cmd`; **does not change `run_all.cmd`**, so existing FORCEGRID and FORCEQUAL remain untouched.

No files are overwritten; tampering or collision results in refusal.

## Geometry trajectories and material correspondence

The `trajectory` command reports a physical radius from each component's length *ratio*, given explicit reference radius, without inventing a metre scale for the coordinates. With `--meters-per-coordinate-unit` it can also report SI length and reference volume. This assumes identical material tubes and a fixed scene scale across all frames. It is a **conditional algebraic reconstruction**, not an independent measurement of core radius or Kelvin conservation. It does not certify that KnotPlot maintains tube material identity.

## Material correspondence comparison

*Only if two XYZ files track the same particles/beads in the same order, without remeshing/reindexing or different component correspondence*:

```bat
run_vccr.cmd compare --initial path\frame0.xyz --final path\frame1.xyz --assert-material-correspondence --meters-per-coordinate-unit 1.0e-15 --a0 1.40897017e-15 --v0 1093845.63 --out Output\VCCR_pair
```

`--meters-per-coordinate-unit` is an explicit physical calibration, not guessed. KnotPlot relaxation typically redistributes beads, so **identical bead indices do not by themselves prove material correspondence**. If correspondence cannot be established, use `geometry` only. The local formula is then *not* valid for a physical Euler analysis.

## Data contract and caution

- Example sources: A006-v0.5.0a's original `KNOT_3_1/5_2/6_1_N0512_ORIG` and `LINK_5_5_6_BALANCED_N0512_ORIG_CPFIXED61`. Also two ASCII conversion files from the user's KnotPlot AMECH N512 experiment. All under `examples/` with SHA256 in `test_manifest.json`.
- The geometric component lengths **cannot** be compared across different A006 seeds as physical lengths without a *shared externally validated scale*. Same applies to a proposed common tube volume across different particle/knot types.
- The model does not calculate geometric reach, actual tube thickness, knot polynomials, link Milnor invariant, or Euler/PKLSA evolution. **No knot stability claims.**
- In the original KnotPlot outputs, `length in short direction = 5.654867` is a KnotPlot geometric scale statement, **not a physical law or automatically an SI length**.
- For the actual knot/link simulation, keep volume and Γ **separately per material tube**. No shared-volume assumption between components unless independently imposed.

Read `SCIENCE_CONTRACT.md` and `FORMULAE.md` for definitions, gates, falsifiers, and validation.
