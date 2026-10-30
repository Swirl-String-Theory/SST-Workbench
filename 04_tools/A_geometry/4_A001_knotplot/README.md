# SST KnotPlot Census — v0.1.2 length-export fix

**Status: independently validated native geometry reconstruction, but catalogue/source identity is not certified.** This is a read-only geometry census, NOT an SST physics or vortex-stability falsifier.

## Observed defect

Your KnotPlot run correctly displays non-zero geometric length after `length`, but `data format "/N,/l"` writes `L_total=0`. A separate diagnostic (`length` immediately before `data`) still writes zero. The cause inside that KnotPlot build is unconfirmed. The documented `/l` field is therefore **not trusted** in this pipeline. We do not modify KnotPlot or incorrectly convert zero to a PASS.

## The fix

1. Each `.kpc` script exports exactly one native `.kpf` **float** and one `ascii` XYZ file, without `data`, `refine`, `ago`, `fitto`, `scale`, `centre`, or other geometric mutators.
2. The Python `audit_native_census_v012.py` reads each KPF's closed components and computes `L=sum(|r[j+1]-r[j]|)` with closing edge. It independently parses ASCII, requires matching component count, vertex count and coordinate parity, and rejects malformed files.
3. Outputs per object: `baseline_geometry_v012.csv`. Per component: `baseline_components_v012.csv`. The old zero metrics stay visible as `LEGACY_LENGTH_INVALID`, never overwritten. `AUDIT_SUMMARY.json` provides the epistemic qualification; `SHA256SUMS.txt` hashes outputs **without self-hashing**.
4. KnotPlot coordinate units are not SI units. The `torus p q` cases remain procedural default-parameter constructs, not immutable catalogue knots, and their N is not automatically adapted to arclength.

## Fastest path: NO rerun needed

`AUDIT_EXISTING_v010.cmd` processes the bundled *original* `falsifier_census_v0.1.0_output.zip` and writes the corrected per-component tables under `audited_v0.1.0_data/`. This result is already included in the package.

## Optional clean rerun from your Workbench

Extract the **contents** of this ZIP to:

`C:\workspace\projects\SST-Workbench\04_tools\A_geometry\A001_knotplot\`

Inside KnotPlot, launched with that directory as the working directory:

```
read Build_Knot_Link_Torus_KnotPlot_Scripts/falsifier_census_v0.1.2/scripts/census_knot_3.1.kpc
read Build_Knot_Link_Torus_KnotPlot_Scripts/falsifier_census_v0.1.2/scripts/census_link_6.3.3.kpc
read Build_Knot_Link_Torus_KnotPlot_Scripts/falsifier_census_v0.1.2/scripts/census_torus_3.3.kpc
```

Then all 50:

```
read Build_Knot_Link_Torus_KnotPlot_Scripts/falsifier_census_v0.1.2/scripts/RUN_CENSUS_ALL.kpc
```

Finally run `AUDIT_NEW_v012.cmd` from Windows CMD (or run `py -3 audit_native_census_v012.py --census-dir Build_Knot_Link_Torus_KnotPlot_Scripts/falsifier_census_v0.1.2 --out audited_v0.1.2_data`). All 50 files must exist; missing or malformed output yields exit code 2 and `UNRESOLVED`.

**Caveats:** `reset all` reinitializes KnotPlot default parameters before each `torus p q`. The generated geometry can differ across KnotPlot builds; record the build version, `N-torus`, and configuration for identity provenance. No bead resampling or physics convergence is performed here.

## Provenance and safeguard

- `falsifier_census_v0.1.0_output.zip` is retained byte-for-byte.
- Earlier audit v0.1.1 remains untouched.
- `data /l=0` is treated as **upstream CSV defect**, not evidence of a zero-length knot.
- Float32 KPF coordinates are an independently saved geometry representation, not proof of bit-exact in-memory length.
- `KnotPlot_catalogue_identity=UNVERIFIED` and `scientific_finite_core_convergence=NOT_TESTED` are mandatory labels in the audit summary.
- The new census scripts are intended to work with the same KnotPlot version as your earlier v0.1.0 run; they have not been executed against your Windows KnotPlot instance here.

### Reference

R. Scharein, KnotPlot Manual, *New KnotPlot Commands* (2017), https://knotplot.com/man/ — documents `data`, `/l`, and the requirement to calculate observables first.
