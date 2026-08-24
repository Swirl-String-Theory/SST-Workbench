# Preregistration — Trefoil Balance Point Campaign v0.1.0

Exactly **10 frozen q/h/p settings × 2 trefoil embeddings = 20 runs**.

Embeddings:

```text
K31: load 3.1
T23: torus 2 3 300
```

All non-q/h/p runtime parameters are copied exactly from the Atlas v0.3.3 baseline.

Frozen q/h/p settings:

```text
B00   15.000000   1.000000   5.00
R25   20.567616   1.089091   5.25
R50   26.135232   1.178183   5.50
R75   31.702848   1.267274   5.75
R100  37.270464   1.356366   6.00
QLO   21.500000   1.000000   5.50
QCEN  23.540000   1.000000   5.50
QHI   25.500000   1.000000   5.50
HLO   26.135232   1.050000   5.50
HHI   26.135232   1.300000   5.50
```

Checkpoints:

\[
i=\{0,25,100,500,1000,4000,10000\}.
\]

Signed geometry-response observable:

\[
E(i)=\frac12\left[\frac{L(i)-L(0)}{L(0)}+\frac{R_g(i)-R_g(0)}{R_g(0)}\right].
\]

Early response is the least-squares slope through iterations 0, 25 and 100,
reported per 100 iterations.

Primary interpretation:
a candidate is more balance-like when the early signed response is close to
zero in **both** trefoil embeddings.

Frozen bracket searches:

1. `QLO/QCEN/QHI`: charge zero crossing at fixed `hooke=1,power=5.5`.
2. `HLO/R50/HHI`: hooke zero crossing at fixed
   `charge=26.135232...,power=5.5`.

This campaign can find a reproducible geometric expansion/contraction zero.
It does **not** by itself prove mechanical `F_expand + F_contract = 0` or
restoring stability. A later geometry-perturbation campaign is required.
