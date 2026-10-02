# Result Check Addendum

Status: the uploaded results validate the corrected v2 framing: Routes A--D are algebraic representations of one seed relation, not four independent derivations.

Small metadata correction: in the uploaded JSON, `seed_relation.G_ratio`, `t_seed`, and `t_ratio` tracked the route-C value rather than the fully reduced `G_seed` value. The fixed JSON distinguishes both:
- `G_seed/G_N = 0.994284248000624`
- `G_route_C/G_N = 0.994284349704464`
- `t(G_seed)/t_p = 0.997138028560050`
- `t(G_route_C)/t_p = 0.997138079557924`

The difference is only the already-disclosed constant-synchronization mismatch:
`G_seed/G_route_C = 0.999999897711514`.

---

# Route A--D Equivalence and Look-Elsewhere Audit

Status: [RESEARCH-TRACK] [TRIAL] [NOT DERIVED] [FITTED].

## Executive correction

The four Planck-route candidates are not four independent confirmations. They are four algebraic representations of one seed relation, once the SST hbar/core closures are used. The previous 'common residual' framing is therefore removed.

## Single seed relation

G_* = (pi^3/16) rho_f vchar^9 r_c^4 /(M_e^2 c^7)
    = 6.636151356430562e-11 m^3 kg^-1 s^-2
G_*/G_N = 0.994284248000624
t_p(G_*) = 5.375817128247970e-44 s
t_p(G_*)/t_p = 0.997138079557924

Equivalent alpha/hbar form:
G_* = (pi^3/2^17) alpha^13 rho_f hbar^4/(M_e^6 c^2), with alpha=2 vchar/c.

## Equivalence checks

B / [2 r_c^2 A] = 1.000000000000000
2 A hbar G_C / c^3 = 0.999999992829592
D / [c^4/(4G_C)] = 1.000000000000000
G_seed / G_C = 0.999999897711514


### Constant-synchronization note

The route-C script value is `G_C = 6.636152035232503e-11`. The fully reduced horn-density seed value is `G_* = 6.636151356430562e-11`. Their ratio is `0.999999897712`. This tiny mismatch is not physics; it comes from the already-noted constant synchronization issue: the explicit `rho_core` used in scripts differs from `M_e c^2/(2 pi vchar^2 r_c^3)` by `1.023e-07`, and the Compton-core hbar closure differs from CODATA hbar by `7.170e-09`.

## Look-elsewhere disclosure

Scan family: G = G0 (rho_f/rho_core)^k (v/c)^n pi^p 2^m.
Ranges: k in [-3,3], n in [-20,20], p in [-8,8], m in [-12,12].
Total grid points: 121975.
Candidates within 5% of G_N: 31.
Candidates within 0.575% of G_N: 5.
Best hit: k=0, n=15, p=-6, m=7, rel_error=-1.702732087162e-03.

## Degeneracy disclosure

Exact closure of the seed relation to G_N requires rho_f = 7.040240267384393e-07 kg m^-3, i.e. 1.005748609626 times the current rounded value 7.0e-7.
Because the alpha/hbar form scales as alpha^13, a fractional alpha shift of 4.410239250519e-04 (0.044102%) absorbs the residual.

## Interpretation

The pack is useful as a target generator for the missing vacuum-tangle theorem, not as proof. The real nontrivial task is to derive rho_f, the exponent structure, and the angular/kernel normalization independently from SST vacuum statistics or pressure susceptibility.
