# Einstein–SST Emergent Metric and Poisson Closure Gates

**Campaign verdict:** `FAIL`

This package tests the *direct* closure chain on relaxed knot centerlines after a preregistered regularized Biot–Savart reconstruction. A FAIL falsifies this direct mapping for that reconstruction; it does not falsify all possible SST long-range closures.

## Headline hypotheses

1. $\Phi_{\rm SST}=-v^2/2$ plus a Newtonian monopole requires $v^2\propto 1/r$ (equivalently $v\propto r^{-1/2}$).
2. If $p/\rho_f\simeq\Phi_{\rm SST}$, then $\int_V[\tfrac12|\omega|^2-S\!:\!S]dV$ must approach $4\pi GM\neq0$ and agree with the monopole inferred from $v^2$.

## Per-knot revealed gates

| blind_id       | source_name       |   ropelength_estimate |   tail_v2_exponent |   tail_mu_poisson_log_slope |   tail_poisson_to_amp_ratio | monopole_1_over_r   | pressure_poisson_monopole   | pressure_phi_closure   | overall   |
|:---------------|:------------------|----------------------:|-------------------:|----------------------------:|----------------------------:|:--------------------|:----------------------------|:-----------------------|:----------|
| K_748D50CBD24B | knot_0.1_final    |               22.1855 |            5.99218 |                    -4.99253 |                     6.00037 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_67DCA64D5325 | knot_10.123_final |              225.45   |            5.99916 |                    -4.99918 |                     6.00003 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_636F57E75791 | knot_10.1_final   |              222.115  |            6.02043 |                    -5.02741 |                     6.01896 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_09A842E0569A | knot_3.1_final    |               90.2491 |            5.99884 |                    -4.99896 |                     6.00012 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_850078665DBC | knot_4.1_final    |              154.743  |            6.05383 |                    -5.07126 |                     6.04981 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_7038F5A6042C | knot_5.1_final    |              127.676  |            6.00157 |                    -5.0024  |                     6.00211 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_358E1A9A4527 | knot_5.2_final    |              158.501  |            6.17915 |                    -5.23181 |                     6.16702 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_BD3CD778D62A | knot_6.1_final    |              177.548  |            6.02882 |                    -5.03886 |                     6.02643 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_3E9F74D6D136 | knot_6.2_final    |              171.155  |            6.00906 |                    -5.01228 |                     6.00877 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_561E6B0C9EF9 | knot_6.3_final    |              155.989  |            6.00222 |                    -5.00326 |                     6.00266 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_E35267BA16F5 | knot_7.1_final    |              146.689  |            6.00059 |                    -5.00109 |                     6.00119 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_80115DEE62C2 | knot_7.2_final    |              154.924  |            6.02972 |                    -5.04097 |                     6.02704 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_618679E87B08 | knot_7.3_final    |              159.436  |            6.04114 |                    -5.05467 |                     6.03821 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_45123D0A11E0 | knot_7.4_final    |              172.815  |            6.11336 |                    -5.1501  |                     6.10405 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_3719FE6CF7F3 | knot_8.17_final   |              198.193  |            6.00043 |                    -5.00081 |                     6.00094 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_7FCE20C0D942 | knot_8.18_final   |              193.362  |            5.99911 |                    -4.99916 |                     6.00005 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_01EF1A6D0EDD | knot_8.1_final    |              219.723  |            6.03652 |                    -5.04882 |                     6.03358 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_8DC4886E5889 | knot_9.1_final    |              173.582  |            5.99948 |                    -4.99965 |                     6.00018 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_F596C587BC92 | knot_9.2_final    |              225.404  |            6.01279 |                    -5.01727 |                     6.01202 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_022A555CD803 | knot_9.35_final   |              233.671  |            6.00881 |                    -5.01425 |                     6.00695 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_9F1C7BBCF48D | link_0.2.1_final  |             1439.86   |            6.00253 |                    -5.00356 |                     6.00218 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_5338971BFF6D | link_0.3.1_final  |             6211.97   |            6.01249 |                    -5.01665 |                     6.01137 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_BD5C87299F3E | link_2.2.1_final  |             2022.05   |            6.01575 |                    -5.02105 |                     6.0143  | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_6E9B542696F7 | link_4.2.1_final  |             1966.45   |            7.3684  |                    -6.48757 |                     7.38124 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_8A7BC76626D2 | link_5.2.1_final  |             2032.34   |            6.01879 |                    -5.02503 |                     6.01711 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_6D78DE897C78 | link_6.2.1_final  |             2089.97   |            6.00125 |                    -5.00171 |                     6.00112 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_6041FDFA8F9E | link_6.3.1_final  |             1961.79   |            6.06662 |                    -5.08793 |                     6.06105 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_CFB668027E58 | link_6.3.2_final  |             2005.19   |            6.04723 |                    -5.06253 |                     6.04319 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_EE26043CACA9 | link_6.3.3_final  |             2463.41   |            6.11189 |                    -5.14634 |                     6.10321 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_D6EDFA1B8DB1 | link_7.2.5_final  |             1990.53   |            6.13256 |                    -5.17291 |                     6.12247 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_7B1A65A00864 | link_7.2.6_final  |             5476.91   |            6.01866 |                    -5.02487 |                     6.01698 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_AF7A1C1F902C | link_7.2.8_final  |             1926.65   |            6.00539 |                    -5.00723 |                     6.00488 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_0AD82E5DD387 | link_8.2.1_final  |             1941.19   |            6.03874 |                    -5.05174 |                     6.03514 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_A4BC4F5443C5 | link_9.2.20_final |             1933.25   |            6.04361 |                    -5.05876 |                     6.03923 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_F6D2C3B98DE5 | link_9.2.40_final |             2453.41   |            6.02043 |                    -5.03274 |                     6.01504 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_AD0937D636A0 | torus_2.11_final  |              206.022  |            5.99968 |                    -4.99986 |                     6.00019 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_776C03DD68BB | torus_2.3_final   |              100.429  |            5.99909 |                    -4.99921 |                     6.00012 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_7D6BD59FA0AD | torus_2.4_final   |             2109.08   |            6.00157 |                    -5.00214 |                     6.00141 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_6E59569148E0 | torus_2.5_final   |              131.591  |            5.99924 |                    -4.99935 |                     6.00012 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_C2010E752023 | torus_2.6_final   |             3369.05   |            6.00109 |                    -5.00151 |                     6.00097 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_8DE9E57FC226 | torus_2.7_final   |              156.152  |            5.99939 |                    -4.99954 |                     6.00015 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_3F1C2FEFC82A | torus_2.8_final   |             2033.27   |            6.00076 |                    -5.00107 |                     6.00065 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_A44DC02B8992 | torus_2.9_final   |              174.068  |            5.99949 |                    -4.99966 |                     6.00018 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_9A8DB49B5D79 | torus_3.3_final   |             1063.25   |            6.00004 |                    -5.0001  |                     6.00006 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_A63D60BD324B | torus_3.6_final   |             1828.88   |            6.00039 |                    -5.00057 |                     6.00034 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_2AC991D03267 | torus_3.9_final   |             2028.88   |            6.00085 |                    -5.00118 |                     6.00076 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_73757787973D | torus_6.15_final  |             2041.32   |            6.00024 |                    -5.00037 |                     6.00021 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_4F2305363305 | torus_6.21_final  |             3198.62   |            6.00026 |                    -5.00041 |                     6.0002  | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_2628B62D17F2 | torus_6.9_final   |             1957.54   |            6.00029 |                    -5.00043 |                     6.00026 | FAIL                | FAIL                        | PASS                   | FAIL      |

## Interpretation rules

- `monopole_1_over_r=FAIL`: the reconstructed closed-knot velocity tail does not produce the required $1/r$ potential through $\Phi=-v^2/2$.
- `pressure_poisson_monopole=FAIL`: the pressure-Poisson source integral does not approach the same non-zero monopole strength.
- `pressure_phi_closure=FAIL`: the Bernoulli/Beltrami identification $p/\rho_f\simeq-v^2/2$ is not supported in the far-field integral sense.
- Metric determinant and clock columns are algebraic/consistency diagnostics, not independent evidence.

## Blinding

Measurement is written under salted blind IDs. Source names are joined only during reveal. Thresholds are copied to `preregistered_config.json` before measurement.
