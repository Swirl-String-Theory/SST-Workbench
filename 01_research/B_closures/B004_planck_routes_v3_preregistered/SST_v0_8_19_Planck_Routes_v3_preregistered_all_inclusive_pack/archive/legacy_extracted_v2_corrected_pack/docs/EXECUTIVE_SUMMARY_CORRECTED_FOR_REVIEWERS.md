# Executive Summary for Reviewers: Corrected Planck Routes A--D

## Verdict

The previous four-route framing is not defensible. A, B, C, and D reduce to one algebraic seed relation. This is a useful trial target, not a derivation.

## Corrected core statement

The single seed is

```tex
G_* = \frac{\pi^3}{16}\frac{\rho_f \vchar^9 r_c^4}{M_e^2 c^7}
```

with

```tex
G_*/G_N = 0.994284248001,   t_p(G_*)/t_p = 0.997138079558.
```

The same seed can be rewritten as:

- Route A: horizon piercing density.
- Route B: induced mode count, exactly `N_B = 2 r_c^2 A`.
- Route C: pressure susceptibility.
- Route D: maximum tension, exactly `F_D = c^4/(4G_C)`.


### Constant-synchronization note

The route-C script value is `G_C = 6.636152035232503e-11`. The fully reduced horn-density seed value is `G_* = 6.636151356430562e-11`. Their ratio is `0.999999897712`. This tiny mismatch is not physics; it comes from the already-noted constant synchronization issue: the explicit `rho_core` used in scripts differs from `M_e c^2/(2 pi vchar^2 r_c^3)` by `1.023e-07`, and the Compton-core hbar closure differs from CODATA hbar by `7.170e-09`.

## Look-elsewhere

The scan family contains 121,975 candidates. There are 31 within 5% of `G_N` and 5 within 0.575%. A better hit exists without the density ratio. Therefore the 0.286% Planck-time match is not evidentiary by itself.

## Degeneracy

Exact closure requires `rho_f = 7.040240e-07 kg/m^3`, close to the rounded canonical `7.0e-7`. The alpha-form scales as `alpha^13`; a ~0.044% shift in `vchar/c` absorbs the residual.

## Recommended status

Keep only as:

```tex
[RESEARCH-TRACK] [TRIAL] [NOT DERIVED] [FITTED]
```

Do not canonize as a Planck-time derivation.

## Real next test

Derive `sigma_pierce Lambda_L` independently from SST vacuum-tangle statistics. The target is:

```tex
sigma_pierce Lambda_L = 1/(2 L_p^2) = 1.9140e69 m^-2.
```
