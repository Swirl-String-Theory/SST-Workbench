# VCCR v0.1.0 — Science contract (frozen proposal)

## Definitions and provenance

**Mathematically derived:** For an embedded tube transported materially by incompressible, inviscid Euler flow without forcing, material-volume conservation plus Kelvin's circulation theorem, under circular cross-section/approximate uniform core vorticity hypotheses, leads to a length–radius–vorticity relation. This is established classical mechanics, not novel SST physics.

**SST calibration is an independent hypothesis:** Use `r_c=1.40897017e-15 m` as the reference core radius; `|v_swirl|=1.09384563e6 m/s` as a reference *edge speed* for a Rankine-like uniform core. Use `R_d=16.3714672385` as a numerical **diameter-convention** ideal trefoil approximation, not an exact mathematical theorem. Assume physical core fills this trefoil geometric thickness. Only under these assumptions is `L0=2*r_c*R_d` and `V0=π*r_c²*L0` justified.

**Rankine approximation:** `v_phi(a)=Γ/(2πa)` for edge speed if the core has uniform axial vorticity, `omega=Γ/(πa²)`. These are not claims about A006's actual vorticity profiles.

## Gates

| Gate | Test | Requirement | Status of current release |
|---|---|---|---|
| G0 | SI/algebra | V=πa²L, Γ=ωπa², ℛ_d=L/(2a) | PASS analytically + unit tests |
| G1 | uniform stretch | a/a0=λ^-1/2, omega/omega0=λ, R_d/R_d0=λ^3/2 | PASS analytically + unit tests |
| G2 | material segment volume bookkeeping | every tube segment A_i ℓ_i constant, Γ_i constant | PASS formula only; no verified material particles |
| G3 | cross-sectional circularity/physical radius | measured area, cross-section, and effective normal bundle | UNRESOLVED |
| G4 | knot/link topology and clearance | independent topology identification + true geometric thickness including inter-component distances | NOT_RUN |
| G5 | Kelvin in actual Euler/PKLSA trajectories | independent cross-section vorticity flux measured at all times | NOT_RUN |
| G6 | SST clock link | independently measured internal excitation frequency vs derived a(t)/Γ | NOT_RUN |
| G7 | same material fluid volume across *different knot types* | independent physical reason/measurement | HYPOTHESIS ONLY |
| G8 | reference trefoil core filling and physical scale | independent geometry-to-SI calibration | UNRESOLVED |

## Mathematical countermodels and edge cases

1. **Constant core radius AND constant Γ AND variable L AND incompressible material volume** are incompatible unless the tube changes other structural properties (exchange, nonmaterial boundary, shape variation). The module rejects this as a simultaneous closure.
2. If fluid cross-section becomes elliptic/nonuniform, use `A(s,t)` rather than equating it to πa²; the effective area-radius is `a_eff=sqrt(A/π)`, not necessarily geometric reach.
3. Under nonuniform stretching, local omega scales by the local material stretch, not merely by the total-length ratio.
4. KnotPlot bead indices are not automatically material trajectories. Bead resampling makes naive index-to-index segment conservation invalid.
5. Ridgerunner ropelength tightening is a geometric optimization problem, not an equilibrium of Euler or SST.
6. Across separate components in the Borromean link, independent Γ_i and V_i must be tracked; setting all V_i=V0 is an optional extra hypothesis.
7. Strong curvature/self-contact can make the simple circular embedded-tube model inadmissible. Even an intact centerline may not admit the assumed radius.
8. In compressible/viscous/reconnecting/external-force cases, Kelvin material-tube assumptions can fail.

## Minimal falsifying measurement

Track a genuine material tube from time 0 to t in a finite-core Euler solver without reconnection. Obtain independently (not reconstructed from this closure) its cross-sectional area A(s,t), arclength stretch λ(s,t), and vorticity flux Γ(s,t). Compare
`A(s,t)*λ(s,t)/A(s,0)=1` and `Γ(s,t)/Γ(s,0)=1`.

Pass: invariants converge with spatial and temporal refinement and no self-intersection. Fail: stable, converged residuals incompatible with tolerances **after** solver/calibration/mesh validation; otherwise unresolved. The closure is not itself tested by reconstructing A from λ.

## Reference list
See `references.tex`. No derived volume, Γ, energy, particle-mass, or Swirl Clock claim is physical certification without gates G3–G8.
