# A003 TwistKnot Flow Lab P2 — Standalone UI correction (2026-10-25)

## Cause in P1
P1 loaded `../index.html` in a visible `<iframe>`. The old VortexLab page therefore appeared in the dedicated route, contrary to the design intent. P1 tests checked the URL and assets but did not assert that the original interface was absent.

## P2 correction
- `/twist-flow/` is now its own HTML application and own 3D viewport with **no iframe**.
- It shares the **exact same numerical runtime and libraries** as `/` (`apps/web/src/legacy/vortexlab-runtime.js`, original catalogs, fluid safeguards). The original solver files are **not modified**.
- For compatibility with the still-monolithic runtime, it fetches the **control DOM only** from `/index.html`, inserts it as an invisible backing engine, then loads the original JavaScript assets. The visible page is exclusively the custom Twist Flow interface. This is a transitional adapter, **not** a fully decoupled physics backend service.
- P2 isolates the single filament view: A006 `5_2` native-N1024 default, Biot–Savart, no auto-relax, topology guard enabled, no speculative couplings, free translation, configurable passive tracers/streamlines, live source diagnostics.
- `10^-18 m` remains an allowed numerical input but does **not** mean a physically resolved core. Existing P2 extreme-core checks stay in force.
- No Euler pressure-Poisson solve, finite-core closure, physical cylinder boundary condition or knot stability claim was added.

## Install
Run `npm run check` and `npm start` from `A003_vortexlab/`. Open `http://127.0.0.1:4173/twist-flow/`. The canonical VortexLab remains at `/`. Do not open the HTML via file://.

## Validating
`npm run test:twist-flow` checks the **absence of iframe**, the independent page and the server's routes. A Chromium functional smoke test is provided in `tools/test-twist-flow-browser.py`, and is optional if playwright is installed. If browser start is blocked, report this separately.

## Constraints
This interim UI shares legacy DOM controls behind the scenes. A future clean architectural refactor would expose a documented solver API and replace the hidden compatibility DOM, but that requires dedicated backend extraction and separate physical parity testing.
