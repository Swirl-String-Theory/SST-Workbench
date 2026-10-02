# Validation — infinite solid-body background vortex v0.2.0

## Mathematical normalization

\[
\alpha c r_c=2v_{\circlearrowleft}r_c=\Gamma_0/\pi
\]

is a circulation scale. The associated uniform vorticity is

\[
\zeta_{\rm bg}=\alpha c/r_c=2v_{\circlearrowleft}/r_c,
\]

and in \((r_c,\Gamma_0)\) units:

\[
\zeta_{\rm bg}^*=1/\pi=0.3183098861837907.
\]

## Automated tests

- Python syntax: PASS
- Unit tests: 6/6 PASS
- Ring control: PASS
- Solid-body velocity formula: PASS
- Trefoil intrinsic-residual invariance: PASS

## Quick campaign

The quick paired campaign contains 96 rows. Comparing `zeta*=0` with
`zeta*=1/pi` gives:

\[
\max |\Delta\epsilon_{\rm intrinsic}|=8.33\times10^{-17}.
\]

The old total-velocity-normalized residual changed by as much as approximately
\(1.20\times10^{-3}\), despite an unchanged absolute residual. Therefore v0.2.0
uses the intrinsic residual for the relative-equilibrium gate.

## Short trefoil evolution

For the Winckelmans kernel, resolution 128, fixed sampled reach and 200 steps:

| quantity | `zeta*=0` | `zeta*=1/pi` |
|---|---:|---:|
| intrinsic static residual | 0.235286 | 0.235286 |
| final recurrence error | 0.005844 | 0.005725 |
| relative energy drift | -0.000698 | -0.000679 |
| relative length drift | -0.000715 | -0.000697 |
| fitted rigid rate | 2.982363 | 3.044719 |

The small differences in recurrence/drift are numerical rotation/remeshing
effects. The intrinsic static deformation is unchanged; only the fitted rigid
motion changes materially.

## Verdict

```text
BACKGROUND-FIELD-IMPLEMENTED
DIMENSIONAL-NORMALIZATION-CORRECTED
INTRINSIC-RESIDUAL-GATE-PASS
UNIFORM-SOLID-BODY-STABILIZATION-REJECTED
FINITE-RADIUS-OR-SHEAR-BACKGROUND-REMAINS-OPEN
```
