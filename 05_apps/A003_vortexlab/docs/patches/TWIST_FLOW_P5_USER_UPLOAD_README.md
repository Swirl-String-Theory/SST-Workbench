# TwistKnot Flow Lab P5 — User Upload Exact-Base Repair

**Base:** `/mnt/data/A003_vortexlab(1).zip` (supplied by user).
**Status:** engineering patch / physics not certified / graphics end-to-end test unavailable.

## Verified defects and changes
- Removes fixed 1 µs time step rejection. The user-reported Δt=1.9034355272012943e-7 s is positive, finite, and accepted without raising the step. Checks floating point clock progress.
- No changes to Biot–Savart, LIA, RK4, topology/contact law, Γ, native point count or A006 geometry.
- Adds actual material-label vertex 0 path-length and net displacement (meters), actual max displacement per accepted RK4 step and effective simulated-second/wall-second throughput; these are read-only. An accepted step with no visible motion no longer suggests an animated physics result.
- Twist Flow can select single-component KnotPlot relaxed knots and Gilbert ideal knots as well as A006 twist knots; excludes link catalog categories. Original `index.html` remains untouched.
- The visible streamlines are instantaneous field geometry and may appear while simulation is halted; they do not establish advection.

## Native A006 catalog provenance
- Manifest from uploaded archive named `twist_knot_data.js`: `2ea27ef2de491aa1e6f0433502307132c7a29d7581788c8a01ac83d64515aafd` (STALE, FAIL).
- Actual archive file SHA-256, preserved byte-for-byte: `6284e6031ae5a20727e89362b573064b6f9503a1157d5dbd122baad8362723e7`.
- Manifest updated to record current archive bytes; **does not certify A006 isotopy/closure or geometric correctness**.

## Performance and physical validity
Native N1024 full Biot–Savart is approximately O(N²) per RK4 stage. If Δt~1.9e-7 s, one physical second requires ~5.25 million *accepted* steps, making movement impractical to see in a browser. The demo mode selects higher Γ and the LIA solver but is not evidence for SST dynamics. Source-vs-dynamic N is never silently reduced. `a_sim=1e-18 m` is representable as a parameter, not physically resolved.

## Installation
Use a new folder, no overwrite of existing experiment. From extracted `A003_vortexlab`:
`npm run check`
`npm start`
Then `http://127.0.0.1:4173/twist-flow/`.

## Browser validation
Headless Chromium navigation in this hosted container was blocked with `ERR_BLOCKED_BY_ADMINISTRATOR`; actual moving canvas on the user's machine has not been certified.

## Optional performance demonstration
`Snelle bewegingspreview · N192` is opt-in and uses the **existing** LIA and demo Γ. It explicitly replaces the DYNAMIC sampling grid N with 192, not the original XYZ geometry or its metadata. This may alter knot isotopy and is not qualified. Button toggles back to native resolution and rebuilds the physics state. The original VortexLab root URL and registered benchmarks are unaffected.
