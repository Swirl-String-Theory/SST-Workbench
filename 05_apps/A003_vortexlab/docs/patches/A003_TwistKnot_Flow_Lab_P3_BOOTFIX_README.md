# A003 TwistKnot Flow Lab P3 — engine startup fix

## Root cause

P2 imported ONLY `#stage` from the canonical VortexLab `index.html`. However,
`#ui-right` is a sibling of `#stage`, containing the controls the unchanged
`vortexlab-runtime.js` requires to initialize (`#modeSeg`, `#twistSelect`,
`#bPause`, and hundreds of other elements). The missing controls caused
unhandled null DOM access in runtime bootstrap, leaving Twist Flow unloaded.

## Repair

- Import **every non-script top-level body element** from the canonical HTML.
- Place `#stage` (3D canvas) in the visible Twist Flow viewport.
- Place all other canonical body nodes in the offscreen `#twistLegacyHost` bridge.
- Insert and verify all required controls **before** loading canonical scripts.
- Load script URLs in the exact order declared in the canonical index.
- Do not duplicate or modify any physical solver, knot data, or numerical-safety logic.

## Validation

- Static full-DOM startup contract, original asset paths, and HTTP routes tested.
- Original native-resolution and fluid safety tests rerun.
- Browser E2E execution blocked by host policy `ERR_BLOCKED_BY_ADMINISTRATOR`;
  therefore no claim of graphics runtime PASS is made.

## Deployment

Unpack FULL in a fresh directory and run `npm run check` and `npm start`.
The dedicated route is `http://127.0.0.1:4173/twist-flow/`. The original
VortexLab remains at `/`.

P2's prior error is not caused by missing WebGL, A006 seeds, or physical solver
failure: the P2 page neglected the legacy controls required by its shared engine.
