# A003 — TwistKnot Flow Lab P1 (24 oktober 2026)

## Scope

Standalone **frontend** for **one A006 twist knot at a time**. The physical engine remains the unchanged VortexLab `v7.6.25b-M1-FluidQualification-P2` browser runtime.

Routes on the same HTTP origin:

- `http://127.0.0.1:4173/` — complete VortexLab (unchanged)
- `http://127.0.0.1:4173/twist-flow/` — dedicated TwistKnot Flow Lab
- `http://127.0.0.1:4173/catalog.html` — existing catalog

Use `npm start` at `A003_vortexlab/`. Open the new route. There is **no deployed public internet URL** included; deploying to a public domain requires separate hosting.

## Architecture / same backend

- `apps/web/twist-flow/index.html` and `twist-flow.css`: focused, responsive frontend.
- `apps/web/twist-flow/twist-flow.js`: DOM event adapter for the existing single-origin VortexLab P2 app in a child iframe; no equations copied or reimplemented. It accesses controls via standard events, reads the existing numerical diagnostics, and hides irrelevant legacy panels in the embedded viewport.
- `apps/web/index.html`, `apps/web/src/legacy/vortexlab-runtime.js`, the P2 fluid-qualification code and original catalog assets remain **unchanged**.
- `tools/serve.mjs` supports directory `index.html` routes and redirects `/twist-flow` to `/twist-flow/`; no second port, backend, or physics engine is created.
- `package.json` gains `test:twist-flow` integrated into `npm run check`.

## Default experiment

- Start with A006 `KNOT_5_2_N1024_ORIG`: *candidate geometry*, not independently isotopy-certified.
- One solo vortex, not a two-knot collision; initially paused.
- Full nonlocal Biot–Savart selected, with LIA as alternative; same equations as P2.
- Topology guard enforced in frontend. Auto-relax, analytical potential-flow overlays, ∂V display layers and core-flow lock off. Center lock off (free translation).
- No new pressure-Poisson solve, no new cylindrical no-penetration boundary condition and no new finite-core Euler closure.
- Existing native point-count logic is retained from P1. Existing tracer-budget logic reduces visible tracers automatically as N increases.
- Choose tracers, streamlines, or knot only. Native diagnostic readouts (simulation time, node count, relative length, circulation, gap-to-core) are mirrored, not recomputed.
- The `a_sim` input is in **meters** here; the legacy engine's `sA` uses millimetres, with exact conversion in the frontend. P2 continues to distinguish representable values such as 1e-18 m from physically/numerically resolved core dynamics.
- Native A006 geometries may contain sharp turns or invalid embeddings. No stability certification is implied by display alone.

## Reproducibility and limitations

- Same origin is required for iframe-to-engine DOM access. Do not use `file://`, and do not host only `/twist-flow/` without its sibling `/index.html`, `/src`, and `/data`.
- The heavy A006 Fourier catalog is loaded by the **existing** backend; the first load can take time, especially on lower-end machines.
- The new route does not implement independent fluid physics; code-level parity with the P2 runtime is checked by the existing hash verifier.
- `npm run check` passes source parity, P1 point-count tests, P2 fluid safety tests, and additional route/interface-contract checks.
- Chromium GUI end-to-end test is **NOT RUN / BLOCKED BY ENVIRONMENT** (`ERR_BLOCKED_BY_ADMINISTRATOR` when navigating to a localhost page). The user should run a manual smoke test in their own browser.

## Manual smoke test

1. `npm run check` then `npm start`.
2. Open `/twist-flow/` (wait until status indicates shared P2 ready). Confirm default `5_2` N=1024.
3. Confirm the original VortexLab route is still available.
4. Toggle tracers, streamlines and knot-only; confirm rendering changes without changing vortex topology.
5. Confirm the front panel shows the native N and effective tracer budget.
6. Toggle Biot–Savart/LIA; reset and start. Confirm time changes; pause and verify time stops.
7. Enter `1e-18` metres in `a_sim`. Confirm numerical qualification warnings; do **not** treat the result as resolved core physics.
8. Confirm invalid A006 twist candidates show warnings when the guard triggers; do not disable the topology guard.
