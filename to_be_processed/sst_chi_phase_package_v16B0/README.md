# SST chi-phase package v16B.0 — patched G5 audit

This patched v16B.0 keeps the useful Madelung derivation but corrects the
status label.

## Main result

If the resolved SST core is accepted as a single coherent Madelung/GP envelope

```text
Psi = F exp(i Theta),      Theta = n theta,
```

with local energy

```text
E_perp = ∫ [ kappa |grad Psi|^2 + (lambda/2)(1-|Psi|^2)^2 ] d^2x,
```

and healing length

```text
xi^2 = kappa/lambda,
```

then polar reduction gives

```text
L_r = F'^2 r + n^2 F^2/r + 1/2(F^2-1)^2 r.
```

Therefore `A=B=C` and for `n=1` the unit GP/NLSE vortex ODE follows.

## Correct status

```text
G5 is conditionally closed inside the single-modulus Madelung core sector.
G5 is not closed from pre-existing SST filament canon alone unless A1--A3 are
accepted or independently derived.
```

## Not claimed

This package does not canonize:

- `alpha_ring = phi`;
- `alpha_ring = 1.61` exactly;
- `xi = r_c`;
- a Lorentz-clock derivation;
- any identification of `alpha_ring` with the fine-structure constant.

Run:

```bash
python simulate_chi_phase_v16B0.py
```
