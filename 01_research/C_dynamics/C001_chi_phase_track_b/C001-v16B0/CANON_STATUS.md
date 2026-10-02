# CANON STATUS — v16B.0 patched

## Status

**Derived-conditional / G5 audit.**

The algebraic reduction

```text
single coherent Madelung envelope -> A=B=C -> unit GP/NLSE vortex ODE
```

is correct. The stronger claim that this is already derived from pre-existing
SST filament canon is not yet established by this package.

## Gate matrix

| Gate | Result | Status |
|---|---|---|
| G5.1 single complex envelope | required | local-core axiom or still to be derived |
| G5.2 A=B from `|grad Psi|^2` | pass if G5.1 accepted | algebraic |
| G5.3 C=A from `xi^2=kappa/lambda` | pass if GP/Madelung depletion law accepted | normalization theorem |
| G5.4 `xi` to SST `r_c` mapping | not resolved | open |
| G5.5 `alpha_ring` independent of target 1.61 | pass | numerical/theoretical extraction |

## Canon-safe statement

```text
Assuming the single-modulus Madelung resolved-core axiom, Track B derives
alpha_ring^GP = 1.6193509... as the dimensionless ring constant of the unit
GP/NLSE vortex ODE.
```

## Not canonized

- `alpha_ring = phi`;
- exact equality to the legacy value `1.61`;
- `xi = r_c`;
- `alpha_ring = alpha_fs`;
- Lorentz/Swirl-clock derivation from the GP core alone.
