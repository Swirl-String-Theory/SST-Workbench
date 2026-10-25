# Tube thickness + a_probe UX + Twist Flow motion (P6)

**Status:** visualization / UX / interactive throughput — not a physics certification.

## Changes
- Buisdikte-render volgt `a_sim` (`P.a`); optionele `r_kern`-shell; toggle **Toon buisdikte**.
- Geen stille 0.35 mm-vloer; scene-floor 0.01 mm alleen met HUD-disclaimer.
- `nQ` (met lock) en `r_kern` forceren `rebuildTubes`.
- `a_probe`: focus-safe sync, zichtbare statusregel; blijft passief (geen solver/tube).
- Twist Flow bij KnotPlot / A006 (catalog high-N): LIA + N192-preview + **demo-Γ** + tracer reset (geen gefingeerde filament-snelheid).
- Passieve tracers: één Biot–Savart-pass per frame over Σ geaccepteerde Δt (filament blijft per CFL-stap).
- Overlay-waarschuwing wanneer full BS het framebudget overschrijdt.

## Check
`npm run check`
