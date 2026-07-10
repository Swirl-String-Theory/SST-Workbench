# Vortexring Lab v4 — version history

This archive preserves the complete HTML development sequence from the original v3 simulator through the current v4 step-12 build.

## Recommended entry points

- `versions/16_current_v4.html` — current consolidated version.
- `versions/00_v3_baseline.html` — original baseline.
- `versions/01...15...html` — curated chronological milestones.
- `raw_snapshots/` — every named before/after HTML snapshot that was retained during development.
- `MANIFEST_SHA256.txt` — SHA-256 hashes for integrity and duplicate detection.

## Chronological changes

1. **Step 1 — particle angular-velocity hue**  
   Tracer color responds to local angular velocity relative to the cylinder.

2. **Step 2.1 — physics overlay close fix**  
   Fixed the physics overlay so it can be closed reliably.

3. **Step 2 — reset button and adaptive hue contrast**  
   Reset moved to the top; tracer hue uses an adaptive relative-vorticity scale.

4. **Step 3 — transparent Taylor/Stewartson geometry**  
   Reduced opacity of Taylor caps, column, separatrix, and Stewartson layer.

5. **Step 4 — dropdown grouping**  
   Consolidated related UI controls and presets into collapsible/dropdown groups.

6. **Step 5 — extra topologies**  
   Added Hopf link `2_2`, figure-eight `4_1`, cinquefoil `5_1`, and `5_2` representations.

7. **Step 6 — numeric inputs with increment controls**  
   Replaced slider-only controls with linked number inputs and increment/decrement controls.

8. **Step 7 — full-height Taylor column**  
   Extended idealized Taylor caps/column over the complete cylinder height.

9. **Step 8 — configurable particle count**  
   Added runtime tracer-count input and buffer rebuilding.

10. **Step 9 — variable cylinder height and linked volume**  
    Added cylinder half-height and diameter–height constant-volume coupling; enlarged parameter ranges and added compact slider+number rows.

11. **Step 9.1 — cylinder scaling no longer deforms knots**  
    Cylinder/tracer geometry may scale while vortex knots retain their own geometry.

12. **Step 10 — absolute centered coordinates and Taylor-column particle reset**  
    Cylinder spans `z=-h` to `z=+h`; knots retain absolute coordinates; particle reset fills the central axial channel.

13. **Step 11 — stability diagnostics and auto-relax**  
    Added stability score, per-control status glow, mesh/core/contact diagnostics, and optional non-Hamiltonian geometric relaxation.

14. **Step 11.1 — stability time brake, reverse time, and dV layer controls**  
    Effective time acceleration falls toward zero with stability; added approximate reverse-time integration and separate opacity/toggles for separatrix, Taylor column, caps, and Stewartson side layer.

15. **Step 12 — knot interaction, geometric core bound, and stability grouping**  
    Fixed source-filament circulation use and trefoil aiming/mirroring; allowed much smaller core radii with a geometry-dependent upper bound; grouped stability-sensitive controls into Cylinder, Vortex Core, and Vortex Flow.

## Notes

- Several `before-step...` snapshots are byte-identical to the preceding completed step. They are retained intentionally so the full edit trail remains reproducible.
- The HTML files reference Three.js and KaTeX from public CDNs. `ideal_knots_data.js` remains optional where the built-in topology data is insufficient.
- `Auto-relax` is a numerical regularizer, not an orthodox Hamiltonian or Biot–Savart equilibrium solver.
