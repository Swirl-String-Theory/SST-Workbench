# VortexLab v7.6.24f1

## Scope

UI-only hotfix on top of v7.6.24f. No solver, scenario, benchmark-gate, knot-data or research-law changes.

## Bottom HUD

- `#spark` remains a separate SPARK widget and now truly disappears when its `<details>` is closed.
- Added an explicit author-level closed-state rule because the older `display:block!important` spark style overrode the browser's native `<details>` hiding.
- LIVE STABILITEIT, SPEC CLOCK · SNEL, STATS and SPARK can all be dragged by their summary bars.
- A four-pixel motion threshold distinguishes drag from click.
- Click still expands/collapses a widget.
- Double-click on the summary returns a floating widget to the lower dock.
- Floating positions are clamped to the viewport and re-clamped after resize.
- Position, width and expanded/collapsed state persist through `localStorage` key `vortexlab.bottomWidgets.v1`.
- Dragged widgets use a high HUD z-index while the global benchmark status strip remains above them.

## Test-run order

1. SPEC CLOCK · 10-run — quick bootstrap and engine regression.
2. Proxy-decomposition — D0–D14 pipeline validation.
3. Geselecteerde holdouts — only the selected knot catalog sources/topologies.
4. Continuüm N=128–768 — convergence and R22/reach blocker.
5. Volledige confirmatoire suite — release/archive run after the separate runners are satisfactory.

`Stop SPEC CLOCK` stops only the 10-run. `Stop diagnose` stops decomposition, continuum, holdout and full-suite runs.

## Validation

- Inline JavaScript syntax: PASS.
- Static DOM IDs: unique.
- SPARK ID: exactly one.
- Four bottom widgets created.
- Full-suite scenario builder still includes selected holdouts.
- `velocityCore`, `velAll`, `rk4Step` and `topologyClearance`: unchanged from v7.6.24f.

A full interactive pointer-drag/WebGL session was not executed in the container; local browser confirmation remains required.
