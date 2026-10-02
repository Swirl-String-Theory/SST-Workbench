# SST v0.8.19 Planck Routes A--D v3 Audit

Status: [RESEARCH-TRACK] [TRIAL] [NOT DERIVED] [FITTED].

## Executive verdict

The Planck routes A--D are retained as a target-generating audit artifact, not as evidence.  They are algebraic representations of one trial seed relation.  The previous four-route convergence framing is rejected.

## Single seed relation

```text
G_* = (pi^3/16) rho_f vchar^9 r_c^4 /(M_e^2 c^7)
    = 6.636151356430562e-11 m^3 kg^-1 s^-2
G_*/G_N = 0.994284248000624
t_p(G_*) = 5.375816853305867e-44 s
t_p(G_*)/t_p = 0.997138028560050
```

Route-C's unreduced expression gives `G_C = 6.636152035232503e-11` and `G_C/G_N = 0.994284349704464`.  The difference between `G_*` and `G_C` is a constant-synchronization artifact, not physics.

## Equivalence checks

```text
B / [2 r_c^2 A] = 1.000000000000000
2 A hbar G_C / c^3 = 0.999999992829592
D / [c^4/(4G_C)] = 0.999999897711515
G_* / G_C = 0.999999897711514
```

## Look-elsewhere disclosure

```text
Scan family: G = G0 (rho_f/rho_core)^k (v/c)^n pi^p 2^m
Ranges: k=[-3,3], n=[-20,20], p=[-8,8], m=[-12,12]
Grid points: 121975
Hits within 5%: 31
Hits within 0.575%: 5
Best hit: k=0, n=15, p=-6, m=7, rel_error=-1.702732087161651e-03
SST seed rank in top-25: 5 in the current scan output.
```

## Route-A preregistered target

The useful non-circular target is not the scanned formula.  It is:

```text
sigma_pierce * Lambda_L = 1/(2 L_p^2)
                          = 1.914036558578934e+69 m^-2
```

The next valid move is to derive `Lambda_L` and `sigma_pierce` independently from a vacuum-tangle model, without using `G`, `L_p`, or `t_p` as inputs.  No further coefficient search should be counted as evidence.

## Degeneracy disclosure

```text
rho_f exact for G_N closure = 7.040240267384393e-07 kg m^-3
rho_f exact/current = 1.005748609626342
d ln G_*/d ln alpha_SST = 13
alpha fractional shift needed = 4.410317968674971e-04
```
