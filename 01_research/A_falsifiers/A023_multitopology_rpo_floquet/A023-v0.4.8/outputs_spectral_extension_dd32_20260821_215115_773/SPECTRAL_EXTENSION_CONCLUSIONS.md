# SST v0.4.8 Adaptive Spectral Convergence Extension

Datasets: **127**.

- SPECTRAL_CONVERGED_K32: **6**
- SPECTRAL_CONVERGED_K48: **2**
- SPECTRAL_CONVERGED_K64: **10**
- SPECTRAL_UNRESOLVED_AT_K64: **109**

## Preregistered decision rule

- Baseline: N=720, k_max=16 from v0.4.7 R4 or a recomputed S0.
- Every dataset is evaluated at k_max=24 and 32.
- Only unresolved datasets continue to k_max=48, then k_max=64.
- A stop requires a quasi-monotone contracting 3-point growth tail, <=3% last relative step, stable P2 verdict, no threshold-overlap under the diagnostic power-tail uncertainty proxy, a present k_max basis, <=10% exact-boundary weight, a decayed high-k Kelvin tail, and k_max <= 0.75 of the least-sampled component Nyquist limit.
- The fit g(k_max)=g_inf+c*k_max^{-p} is diagnostic only and cannot by itself create convergence.
- SPECTRAL_UNRESOLVED_AT_K64 is a valid falsifier outcome; it is not coerced into PASS/FAIL.

## Results

| source | classification | P2 | k | g | tail ratio | last rel | boundary | high-k tail | reasons |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| knotplot:link_2.2.1 | SPECTRAL_CONVERGED_K32 | PASS | 32 | 0.005876163 | 0.3002 | 0.02038 | 0.008077 | 0.04908 |  |
| knotplot:knot_5.2 | SPECTRAL_CONVERGED_K64 | PASS | 64 | 0.01311315 | 0.2528 | 0.017 | 0.006024 | 0.03383 |  |
| knotplot:link_5.2.1 | SPECTRAL_CONVERGED_K64 | PASS | 64 | 0.01594405 | 0.4187 | 0.02463 | 0.003878 | 0.0395 |  |
| knotplot:knot_6.3 | SPECTRAL_CONVERGED_K64 | PASS | 64 | 0.01837818 | 0.2296 | 0.02303 | 0.002034 | 0.03526 |  |
| knotplot:knot_7.4 | SPECTRAL_CONVERGED_K64 | PASS | 64 | 0.01851141 | 0.3196 | 0.02493 | 0.00189 | 0.02308 |  |
| knotplot:link_8.2.1 | SPECTRAL_CONVERGED_K64 | PASS | 64 | 0.02123962 | 0.4719 | 0.01497 | 0.0001777 | 0.003017 |  |
| knotplot:link_4.2.1 | SPECTRAL_CONVERGED_K64 | PASS | 64 | 0.02348458 | 0.3916 | 0.01805 | 3.404e-05 | 0.003679 |  |
| knotplot:link_7.2.5 | SPECTRAL_CONVERGED_K64 | PASS | 64 | 0.02385947 | 0.2437 | 0.008753 | 0.00239 | 0.02166 |  |
| knotplot:link_7.2.8 | SPECTRAL_CONVERGED_K64 | PASS | 64 | 0.02554289 | 0.2672 | 0.02432 | 0.002256 | 0.02506 |  |
| knotplot:link_6.3.3 | SPECTRAL_CONVERGED_K64 | PASS | 64 | 0.02621638 | 0.1352 | 0.005594 | 0.0001819 | 0.004325 |  |
| knotplot:link_9.2.40 | SPECTRAL_CONVERGED_K48 | PASS | 48 | 0.02646812 | 0.6617 | 0.02244 | 0.000268 | 0.01781 |  |
| knotplot:knot_6.2 | SPECTRAL_CONVERGED_K64 | PASS | 64 | 0.02793639 | 0.1449 | 0.02979 | 0.00273 | 0.02326 |  |
| knotplot:link_7.2.6 | SPECTRAL_CONVERGED_K32 | PASS | 32 | 0.03011245 | 0.09893 | 0.0147 | 0.005047 | 0.02391 |  |
| knotplot:torus_3.3 | SPECTRAL_CONVERGED_K48 | PASS | 48 | 0.03990988 | 0.4897 | 0.02281 | 0.0002144 | 0.004128 |  |
| knotplot:link_0.2.1 | SPECTRAL_CONVERGED_K32 | PASS | 32 | 0.09450581 | 0.05404 | 0.004979 | 1.421e-11 | 8.571e-10 |  |
| knotplot:link_0.3.1 | SPECTRAL_CONVERGED_K32 | FAIL | 32 | 0.1252926 | 0.0102 | 0.0002031 | 3.26e-11 | 3.358e-08 |  |
| knotplot:knot_0.1 | SPECTRAL_CONVERGED_K32 | FAIL | 32 | 0.3089981 | 0.1406 | 1.776e-07 | 1.994e-09 | 5.353e-08 |  |
| fremlin:1_1:knot.1_1 | SPECTRAL_CONVERGED_K32 | FAIL | 32 | 0.3106918 | 0 | 2.144e-15 | 1.332e-27 | 2.234e-26 |  |
| fremlin:5_2:knot.5_2 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.01925919 | 0.4844 | 0.0358 | 3.478e-06 | 0.0001057 | growth_last_step_too_large |
| knotplot:link_9.2.20 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.02037579 | 0.08482 | 0.002791 | 0.0009936 | 0.01423 | growth_tail_not_quasi_monotone |
| knotplot:knot_7.3 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.022333 | 0.1086 | 0.01098 | 0.001342 | 0.01976 | growth_tail_not_quasi_monotone |
| knotplot:torus_2.4 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.02886978 | 0.3742 | 0.04019 | 0.0002936 | 0.001947 | growth_last_step_too_large |
| knotplot:knot_3.1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.0300671 | 0.5199 | 0.0802 | 0.0006445 | 0.004892 | growth_last_step_too_large |
| knotplot:torus_2.3 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.03048685 | 0.4544 | 0.07652 | 4.692e-08 | 0.006125 | growth_last_step_too_large |
| fremlin:6_2:knot.6_2 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.03098968 | 0.8615 | 0.07545 | 0.0001684 | 0.006661 | growth_tail_not_contracting, growth_last_step_too_large |
| fremlin:3_1:knot.3_1p | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.03118894 | 0.4459 | 0.08016 | 7.981e-28 | 0.002102 | growth_last_step_too_large |
| knotplot:link_6.2.1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.03242809 | 0.3947 | 0.05444 | 0.0001098 | 0.001659 | growth_last_step_too_large |
| fremlin:8_2:knot.8_2 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.03339444 | 0.4911 | 0.08265 | 0.005978 | 0.02931 | growth_last_step_too_large |
| knotplot:knot_7.2 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.03388509 | 0.507 | 0.03635 | 0.001196 | 0.05893 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:7_2:knot.7_2 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.03455715 | 0.504 | 0.05905 | 1.336e-27 | 0.00519 | growth_last_step_too_large |
| knotplot:knot_9.35 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.03654461 | 0.4481 | 0.05629 | 0.0005815 | 0.01862 | growth_last_step_too_large |
| fremlin:4_1:knot.4_1z | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.03753921 | 0.5464 | 0.0967 | 0.005529 | 0.01646 | growth_last_step_too_large |
| knotplot:knot_4.1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.03768858 | 0.2213 | 0.03161 | 0.002807 | 0.05115 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| knotplot:link_6.3.2 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.03808091 | 0.1615 | 0.005749 | 0.01315 | 0.0775 | high_k_mode_tail_not_decayed |
| fremlin:3_1:knot.3_1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.03855773 | 0.451 | 0.1066 | 2.597e-28 | 0.0001121 | growth_last_step_too_large |
| knotplot:knot_8.17 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.03935256 | 0.3472 | 0.06179 | 0.004643 | 0.07678 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:10_1:knot.10_1n | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.03972513 | 0.5894 | 0.0298 | 0.02055 | 0.3436 | high_k_mode_tail_not_decayed |
| knotplot:link_6.3.1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.04032116 | 1.134 | 0.05026 | 0.0008559 | 0.02841 | growth_tail_not_contracting, growth_last_step_too_large |
| fremlin:6_1:knot.6_1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.04039212 | 0.4355 | 0.08731 | 0.0003782 | 0.004575 | growth_last_step_too_large |
| knotplot:knot_5.1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.04099352 | 0.452 | 0.1361 | 6.127e-05 | 0.001887 | growth_last_step_too_large |
| knotplot:torus_2.6 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.04110446 | 0.3968 | 0.06811 | 4.319e-07 | 0.0002182 | growth_last_step_too_large |
| fremlin:8_18:knot.8_18z | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.04346236 | 0.5104 | 0.29 | 1.321e-27 | 0.05374 | growth_last_step_too_large, P2_verdict_changed_across_tail, high_k_mode_tail_not_decayed |
| fremlin:9_2:knot.9_2n | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.04445005 | 0.8627 | 0.06899 | 0.0006401 | 0.01526 | growth_tail_not_contracting, growth_last_step_too_large |
| fremlin:7_3:knot.7_3 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.0451344 | 0.4494 | 0.09944 | 0.0002827 | 0.003073 | growth_last_step_too_large |
| knotplot:knot_9.2 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.0454002 | 0.3893 | 0.07695 | 1.483e-05 | 0.03443 | growth_last_step_too_large |
| knotplot:knot_8.18 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.04595093 | 0.03573 | 0.01341 | 0.02008 | 0.1136 | high_k_mode_tail_not_decayed |
| knotplot:knot_8.1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.04628575 | 19.71 | 0.1667 | 0.001669 | 0.03414 | growth_tail_not_quasi_monotone, growth_tail_not_contracting, growth_last_step_too_large |
| knotplot:knot_6.1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.04717797 | 1.242 | 0.1321 | 0.0009611 | 0.0394 | growth_tail_not_quasi_monotone, growth_tail_not_contracting, growth_last_step_too_large |
| knotplot:knot_10.123 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.04797723 | 0.1334 | 0.04512 | 0.003184 | 0.05355 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| knotplot:knot_10.1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.04830055 | 0.6922 | 0.03247 | 0.00157 | 0.04028 | growth_last_step_too_large |
| knotplot:knot_7.1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.04875881 | 0.4806 | 0.1855 | 0.0002256 | 0.003974 | growth_last_step_too_large |
| fremlin:7_5:knot.7_5 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.04903939 | 0.6221 | 0.1121 | 0.001797 | 0.01571 | growth_last_step_too_large |
| fremlin:4_1:knot.4_1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.04933839 | 0.3545 | 0.1079 | 0.001653 | 0.007712 | growth_last_step_too_large |
| knotplot:torus_2.8 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.04993085 | 0.3755 | 0.08066 | 8.252e-05 | 0.0003716 | growth_last_step_too_large |
| fremlin:3_1:knot.3_1u | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.05150385 | 0.4221 | 0.1261 | 9.07e-07 | 1.183e-05 | growth_last_step_too_large |
| fremlin:8_3:knot.8_3z | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.05314445 | 0.5503 | 0.2377 | 0.0006172 | 0.009192 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| fremlin:7_6:knot.7_6s | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.05481626 | 1.349 | 0.3798 | 0.002185 | 0.02114 | growth_tail_not_contracting, growth_last_step_too_large, P2_verdict_changed_across_tail |
| knotplot:torus_2.5 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.05796484 | 0.5557 | 0.1737 | 7.931e-11 | 0.002307 | growth_last_step_too_large |
| fremlin:8_19:knot.8_19u | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.05973129 | 0.3969 | 0.1684 | 2.105e-28 | 0.0006374 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| fremlin:8_10:knot.8_10s | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.05997152 | 0.2361 | 0.1009 | 0.003282 | 0.03263 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| fremlin:8_5:knot.8_5 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.06033916 | 0.3372 | 0.1829 | 0.0008244 | 0.02467 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| fremlin:5_1:knot.5_1p | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.06081391 | 0.3226 | 0.1021 | 6.341e-28 | 0.002283 | growth_last_step_too_large |
| fremlin:8_17:knot.8_17 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.06212371 | 0.4867 | 0.1944 | 0.001097 | 0.02742 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| knotplot:torus_3.6 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.06361366 | 0.2853 | 0.06064 | 0.00426 | 0.01403 | growth_last_step_too_large |
| knotplot:torus_3.9 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.06374591 | 0.3674 | 0.05841 | 0.0001832 | 0.00394 | growth_last_step_too_large |
| fremlin:8_6:knot.8_6 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.06681935 | 0.6117 | 0.2848 | 0.002628 | 0.01775 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| fremlin:8_1:knot.8_1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.06844283 | 0.4694 | 0.1833 | 0.0006175 | 0.01078 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| fremlin:8_19:knot.8_19t | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.06902791 | 0.5455 | 0.1696 | 0.0002567 | 0.002036 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| fremlin:8_7:knot.8_7s | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.07088816 | 1.531 | 0.2383 | 0.002936 | 0.02825 | growth_tail_not_contracting, growth_last_step_too_large |
| fremlin:6_3:knot.6_3z | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.07600305 | 0.3418 | 0.2197 | 1.691e-28 | 0.003119 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| fremlin:7_1:knot.7_1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.07654922 | 0.4562 | 0.2756 | 2.532e-11 | 3.668e-05 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| fremlin:5_1:knot.5_1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.07714913 | 0.6244 | 0.2684 | 2.086e-10 | 0.0001411 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| knotplot:torus_2.7 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.08031825 | 0.5498 | 0.2886 | 6.076e-06 | 0.0001967 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| fremlin:12a_1202:knot.12a_1202z6 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.0960022 | 0.5194 | 0.3391 | 0.001406 | 0.03867 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| fremlin:8_11:knot.8_11 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.101032 | 0.4224 | 0.2962 | 6.899e-05 | 0.004768 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| fremlin:7_1:knot.7_1p | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.1030158 | 0.4382 | 0.2108 | 4.228e-07 | 0.001193 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| fremlin:15331:knot.15331 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.1042746 | 0.7938 | 0.2759 | 0.004837 | 0.1095 | growth_tail_not_quasi_monotone, growth_tail_not_contracting, growth_last_step_too_large, P2_verdict_changed_across_tail, high_k_mode_tail_not_decayed |
| knotplot:torus_2.9 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.1051656 | 0.6263 | 0.4173 | 7.484e-06 | 9.176e-05 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| knotplot:knot_9.1 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.1051671 | 0.6263 | 0.4173 | 8.149e-06 | 9.444e-05 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| knotplot:torus_6.9 | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.1115031 | 1.606 | 0.1642 | 0.0003254 | 0.009032 | growth_tail_not_contracting, growth_last_step_too_large, P2_verdict_changed_across_tail |
| fremlin:8_12:knot.8_12z | SPECTRAL_UNRESOLVED_AT_K64 | PASS | 64 | 0.1195249 | 0.3049 | 0.4875 | 1.431e-27 | 0.004364 | growth_last_step_too_large, P2_verdict_changed_across_tail |
| knotplot:torus_2.11 | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.1417979 | 0.9763 | 0.5806 | 1.66e-07 | 3.694e-05 | growth_tail_not_contracting, growth_last_step_too_large |
| knotplot:torus_6.15 | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.1575103 | 0.2079 | 0.04612 | 0.0002566 | 0.00906 | growth_last_step_too_large |
| fremlin:5_1:knot.5_1u | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.1623396 | 0.4129 | 0.4939 | 5.858e-29 | 2.139e-08 | growth_last_step_too_large |
| fremlin:8_3:knot.8_3 | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.1704006 | 0.3806 | 0.4587 | 0.0003879 | 0.006248 | growth_last_step_too_large |
| fremlin:8_18:knot.8_18 | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.2023932 | 0.1283 | 0.08529 | 0.0001819 | 0.05447 | growth_tail_not_quasi_monotone, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_15:knot.8_15 | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.2083957 | 0.2382 | 0.2774 | 0.003375 | 0.1678 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_21:knot.8_21r | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.2229158 | 2.236 | 0.2283 | 0.00151 | 0.07896 | growth_tail_not_contracting, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:5_2:knot.5_2d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.2300145 | 0.2238 | 0.06024 | 0.0003953 | 0.258 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_16:knot.8_16 | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.2536488 | 0.5496 | 0.09522 | 0.009932 | 0.0949 | growth_tail_not_quasi_monotone, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_21:knot.8_21d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.254046 | 0.02371 | 0.00846 | 0.01507 | 0.251 | growth_tail_not_quasi_monotone, high_k_mode_tail_not_decayed |
| knotplot:torus_6.21 | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.2668893 | 10.92 | 0.2985 | 0.0004319 | 0.02864 | growth_tail_not_contracting, growth_last_step_too_large |
| fremlin:8_15:knot.8_15p | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.2740993 | 0.4662 | 0.1601 | 0.005866 | 0.1633 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:7_5:knot.7_5d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.289344 | 0.3141 | 0.08574 | 0.0005184 | 0.1523 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:6_3:knot.6_3d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.3127014 | 0.3532 | 0.05085 | 1.981e-05 | 0.02008 | growth_last_step_too_large |
| fremlin:8_11:knot.8_11d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.3144947 | 0.2913 | 0.07646 | 0.03956 | 0.2122 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:4_1:knot.4_1d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.318714 | 0.4478 | 0.13 | 0.002936 | 0.1028 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_8:knot.8_8d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.3220457 | 0.2092 | 0.0638 | 0.02876 | 0.3186 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_1:knot.8_1d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.3293878 | 0.1678 | 0.04001 | 0.006306 | 0.1469 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:6_2:knot.6_2d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.3401956 | 0.7264 | 0.2034 | 0.01442 | 0.3796 | growth_tail_not_quasi_monotone, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_2:knot.8_2d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.3421177 | 0.3586 | 0.01469 | 0.01248 | 0.3697 | high_k_mode_tail_not_decayed |
| fremlin:7_6:knot.7_6d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.358247 | 0.2559 | 0.02059 | 9.562e-05 | 0.1202 | high_k_mode_tail_not_decayed |
| fremlin:10_1:knot.10_1 | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.3751464 | 2.571 | 0.07278 | 0.006122 | 0.1698 | growth_tail_not_contracting, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_3:knot.8_3d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.3902719 | 1.812 | 0.01785 | 0.01792 | 0.2923 | growth_tail_not_contracting, high_k_mode_tail_not_decayed |
| fremlin:12a_1202:knot.12a_1202 | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.3910494 | 0.3505 | 0.145 | 0.002963 | 0.1077 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_7:knot.8_7d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.3931997 | 1.389 | 0.3103 | 0.005755 | 0.1819 | growth_tail_not_quasi_monotone, growth_tail_not_contracting, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:5_2:knot.5_2r | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.4253779 | 0.2432 | 0.1119 | 0.0006069 | 0.217 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_9:knot.8_9d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.4467287 | 1.249 | 0.2061 | 0.000408 | 0.04533 | growth_tail_not_contracting, growth_last_step_too_large |
| fremlin:8_21:knot.8_21p | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.4609596 | 0.6058 | 0.03752 | 0.0183 | 0.2193 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:7_2:knot.7_2r | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.4664791 | 0.2647 | 0.1117 | 0.000971 | 0.1852 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_15:knot.8_15d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.4803193 | 1.588 | 0.411 | 4.175e-05 | 0.109 | growth_tail_not_contracting, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:6_2:knot.6_2p | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.545368 | 0.2928 | 0.02651 | 0.003319 | 0.1797 | growth_tail_not_quasi_monotone, high_k_mode_tail_not_decayed |
| fremlin:4_1:knot.4_1p | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.5636258 | 1.908 | 0.476 | 0.002797 | 0.1156 | growth_tail_not_contracting, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:7_3:knot.7_3d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.5750047 | 0.805 | 0.03342 | 0.002316 | 0.1825 | growth_tail_not_quasi_monotone, growth_tail_not_contracting, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_14:knot.8_14r | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.5871545 | 0.6354 | 0.2631 | 0.003509 | 0.09528 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_12:knot.8_12d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.6142204 | 0.8493 | 0.2054 | 0.02363 | 0.2624 | growth_tail_not_contracting, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_14:knot.8_14d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.6449896 | 0.7663 | 0.2388 | 0.001069 | 0.136 | growth_tail_not_contracting, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:7_2:knot.7_2d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.7156182 | 1.718 | 0.2204 | 0.00429 | 0.1269 | growth_tail_not_contracting, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:7_7:knot.7_7d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.7289461 | 1.127 | 0.07455 | 0.04611 | 0.2685 | growth_tail_not_quasi_monotone, growth_tail_not_contracting, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:7_4:knot.7_4 | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.7870957 | 4.163 | 0.2115 | 0.006477 | 0.1629 | growth_tail_not_contracting, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_13:knot.8_13d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.7976448 | 0.2271 | 0.01263 | 0.02306 | 0.2445 | growth_tail_not_quasi_monotone, high_k_mode_tail_not_decayed |
| fremlin:8_6:knot.8_6p | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.8522264 | 1.446 | 0.3464 | 0.007025 | 0.1486 | growth_tail_not_contracting, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:9_2:knot.9_2 | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.896285 | 0.9939 | 0.07517 | 0.02347 | 0.2987 | growth_tail_not_quasi_monotone, growth_tail_not_contracting, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_20:knot.8_20r | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.9201983 | inf | 0.08672 | 0.0002804 | 0.04398 | growth_tail_not_quasi_monotone, growth_tail_not_contracting, growth_last_step_too_large |
| fremlin:8_4:knot.8_4d | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 0.9436305 | 2.918e+12 | 0.05974 | 0.006537 | 0.1093 | growth_tail_not_contracting, growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_13:knot.8_13p | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 1 | 0.6553 | 0.1434 | 0.003628 | 0.2505 | growth_last_step_too_large, high_k_mode_tail_not_decayed |
| fremlin:8_4:knot.8_4 | SPECTRAL_UNRESOLVED_AT_K64 | FAIL | 64 | 1 | 2.922e-07 | 7.649e-14 | 0.01855 | 0.2534 | high_k_mode_tail_not_decayed |
