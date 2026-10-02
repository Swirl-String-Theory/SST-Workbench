# Trefoil Balance Point Campaign v0.2.0 — K31 zero bracket

**Overall: `CONTRACT_REGIME_FOUND_HOOKE_ONLY`**

Primary signed response:
\[E(i)=\frac12[(L/L_0-1)+(R_g/R_{g0}-1)]\]

`NEAR_ZERO` threshold: |early E/100| <= 0.0002.

## Lane results

### full_balance_ray_extended
- Status: **NO_ZERO_IN_FROZEN_RANGE**

| setting | scan | q | h | p | early E/100 | class | E@1000 | E@10000 |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| R01 | 1.05 | 38.384 | 1.37418 | 6.05 | 0.00036390788 | INCONSISTENT_TRANSIENT | 0.0077029421 | 0.01112307 |
| R02 | 1.1 | 39.4975 | 1.392 | 6.1 | 1.3818269e-05 | INCONSISTENT_TRANSIENT | 0.0057839537 | 0.0085030185 |
| R03 | 1.15 | 40.611 | 1.40982 | 6.15 | -0.0003382835 | INCONSISTENT_TRANSIENT | 0.0038371452 | 0.0058638746 |
| R04 | 1.2 | 41.7246 | 1.42764 | 6.2 | -0.00069223415 | CONTRACT | 0.0018663889 | 0.0032096103 |
| R05 | 1.25 | 42.8381 | 1.44546 | 6.25 | -0.0010478973 | CONTRACT | -0.00012481626 | 0.00054380743 |
| R06 | 1.35 | 45.0651 | 1.48109 | 6.35 | -0.0017638029 | CONTRACT | -0.0041561698 | -0.0048098318 |
| R07 | 1.5 | 48.4057 | 1.53455 | 6.5 | -0.0028467857 | CONTRACT | -0.010286101 | -0.012855831 |
| R08 | 1.7 | 52.8598 | 1.60582 | 6.7 | -0.004299912 | CONTRACT | -0.018526264 | -0.023526594 |
| R09 | 1.95 | 58.4274 | 1.69491 | 6.95 | -0.0061121126 | CONTRACT | -0.02879676 | -0.036643042 |
| R10 | 2.25 | 65.1085 | 1.80182 | 7.25 | -0.008248481 | CONTRACT | -0.040909932 | -0.051907601 |
| R11 | 2.6 | 72.9032 | 1.92655 | 7.6 | -0.010648904 | CONTRACT | -0.054583392 | -0.068928151 |
| R12 | 3 | 81.8114 | 2.0691 | 8 | -0.013236574 | CONTRACT | -0.069472349 | -0.087259744 |

### hooke_dominant_bracket
- Status: **NO_ZERO_IN_FROZEN_RANGE**

| setting | scan | q | h | p | early E/100 | class | E@1000 | E@10000 |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| H01 | 1.35 | 26.1352 | 1.35 | 5.5 | 0.0018387259 | EXPAND | 0.015860215 | 0.022547824 |
| H02 | 1.4 | 26.1352 | 1.4 | 5.5 | 0.0013404469 | EXPAND | 0.01319163 | 0.01870735 |
| H03 | 1.45 | 26.1352 | 1.45 | 5.5 | 0.00086492706 | EXPAND | 0.0105695 | 0.0150063 |
| H04 | 1.5 | 26.1352 | 1.5 | 5.5 | 0.0004057555 | INCONSISTENT_TRANSIENT | 0.0079934987 | 0.011435568 |
| H05 | 1.6 | 26.1352 | 1.6 | 5.5 | -0.00048076812 | CONTRACT | 0.0029761903 | 0.0046526225 |
| H06 | 1.75 | 26.1352 | 1.75 | 5.5 | -0.0017682311 | CONTRACT | -0.0042302583 | -0.0047295496 |
| H07 | 2 | 26.1352 | 2 | 5.5 | -0.0038722886 | CONTRACT | -0.015464721 | -0.01862132 |
| H08 | 2.4 | 26.1352 | 2.4 | 5.5 | -0.0072054391 | CONTRACT | -0.031691589 | -0.0373952 |

## Decision

- If the joint ray brackets zero: use the interpolated q/h/p as the next refinement center.
- If only the hooke lane reaches CONTRACT: the contractive regime exists, but the previous joint ray is not the correct balance direction.
- If neither reaches CONTRACT: extend the frozen range prospectively in a new version; do not move points post hoc.
- Only after a reproducible zero is found should T(2,3) repeat the same frozen bracket as an independent embedding control.
