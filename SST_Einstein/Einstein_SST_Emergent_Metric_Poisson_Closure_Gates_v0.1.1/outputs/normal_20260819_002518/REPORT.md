# Einstein–SST Emergent Metric and Poisson Closure Gates

**Campaign verdict:** `FAIL`

This package tests the *direct* closure chain on relaxed knot centerlines after a preregistered regularized Biot–Savart reconstruction. A FAIL falsifies this direct mapping for that reconstruction; it does not falsify all possible SST long-range closures.

## Headline hypotheses

1. $\Phi_{\rm SST}=-v^2/2$ plus a Newtonian monopole requires $v^2\propto 1/r$ (equivalently $v\propto r^{-1/2}$).
2. If $p/\rho_f\simeq\Phi_{\rm SST}$, then $\int_V[\tfrac12|\omega|^2-S\!:\!S]dV$ must approach $4\pi GM\neq0$ and agree with the monopole inferred from $v^2$.

## Per-knot revealed gates

| blind_id       | source_name       |   ropelength_estimate |   tail_v2_exponent |   tail_mu_poisson_log_slope |   tail_poisson_to_amp_ratio | monopole_1_over_r   | pressure_poisson_monopole   | pressure_phi_closure   | overall   |
|:---------------|:------------------|----------------------:|-------------------:|----------------------------:|----------------------------:|:--------------------|:----------------------------|:-----------------------|:----------|
| K_C7DC2950788C | knot_0.1_final    |               11.0918 |            5.96824 |                    -4.96847 |                     6.00025 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_DD2C03CF417B | knot_10.123_final |              114.561  |            5.99675 |                    -4.99676 |                     6.00002 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_19B368E59AED | knot_10.1_final   |              112.508  |            6.01859 |                    -5.02536 |                     6.01839 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_1ABDAABA12B6 | knot_3.1_final    |               49.0079 |            5.99577 |                    -4.99588 |                     6.00011 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_CF92E1071C76 | knot_4.1_final    |               78.3236 |            6.05086 |                    -5.0678  |                     6.04836 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_A566B1DEB66D | knot_5.1_final    |               64.1484 |            5.99927 |                    -5.00008 |                     6.00204 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_1CC11752EECA | knot_5.2_final    |               82.4306 |            6.17281 |                    -5.22415 |                     6.16213 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_CC8D0845368D | knot_6.1_final    |               88.04   |            6.0266  |                    -5.03632 |                     6.02562 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_457F54DE2A46 | knot_6.2_final    |               80.6791 |            6.00685 |                    -5.00996 |                     6.00849 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_E74E631130C7 | knot_6.3_final    |               78.4112 |            5.99996 |                    -5.00097 |                     6.00254 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_6F91A8F13F8F | knot_7.1_final    |               76.7956 |            5.99865 |                    -4.99913 |                     6.00116 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_8DCAD088F6D8 | knot_7.2_final    |               82.5134 |            6.02681 |                    -5.03764 |                     6.02612 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_4C76167C01D3 | knot_7.3_final    |               80.4846 |            6.03809 |                    -5.05121 |                     6.03696 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_0DDAE583D000 | knot_7.4_final    |               86.9086 |            6.10813 |                    -5.14379 |                     6.10077 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_A7D0AE82EEEB | knot_8.17_final   |              101.679  |            5.99871 |                    -4.99907 |                     6.00089 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_1FB86F8EC279 | knot_8.18_final   |               97.118  |            5.99637 |                    -4.99642 |                     6.00004 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_1931167FB8EF | knot_8.1_final    |              109.816  |            6.03426 |                    -5.04619 |                     6.03259 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_407A28D944DF | knot_9.1_final    |               87.0744 |            5.99727 |                    -4.99743 |                     6.00017 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_AC366EE8697E | knot_9.2_final    |              112.65   |            6.01108 |                    -5.01542 |                     6.01165 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_D51FC05BAC2B | knot_9.35_final   |              126.522  |            6.00724 |                    -5.01238 |                     6.00659 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_1CABF6170165 | link_0.2.1_final  |              719.369  |            6.00241 |                    -5.0034  |                     6.00209 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_E53BF3CE0FCA | link_0.3.1_final  |             6209.95   |            6.01209 |                    -5.01612 |                     6.01099 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_27FC810CAF76 | link_2.2.1_final  |             1022.87   |            6.01528 |                    -5.02042 |                     6.01387 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_C75E13C6350E | link_4.2.1_final  |             1014.08   |            7.35443 |                    -6.47481 |                     7.36712 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_6D8C79729892 | link_5.2.1_final  |             1011.87   |            6.01815 |                    -5.0242  |                     6.01651 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_BF0B5AA47131 | link_6.2.1_final  |             2089.12   |            6.00121 |                    -5.00166 |                     6.00108 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_E2CA4F9C0BB3 | link_6.3.1_final  |              980.96   |            6.06471 |                    -5.08544 |                     6.05924 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_6CA7D1A711CE | link_6.3.2_final  |             1544.92   |            6.04594 |                    -5.06082 |                     6.04198 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_CD95A81CD2CF | link_6.3.3_final  |             2459.27   |            6.1087  |                    -5.14223 |                     6.10012 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_87FA62BBE542 | link_7.2.5_final  |              924.302  |            6.12873 |                    -5.16801 |                     6.11878 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_E57EDBD0D445 | link_7.2.6_final  |             5472.66   |            6.01806 |                    -5.02408 |                     6.01642 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_BD44E8868E58 | link_7.2.8_final  |              964.53   |            6.00519 |                    -5.00697 |                     6.00472 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_556812E2D5CC | link_8.2.1_final  |             1500.44   |            6.03761 |                    -5.05021 |                     6.03409 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_7E39AC7E0592 | link_9.2.20_final |             1008.64   |            6.04212 |                    -5.05675 |                     6.03786 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_5C903FE7DD28 | link_9.2.40_final |             2451.97   |            6.01922 |                    -5.0308  |                     6.01412 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_4B4AB76061B2 | torus_2.11_final  |              101.014  |            5.99784 |                    -4.99802 |                     6.00018 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_2CE36F5EEB80 | torus_2.3_final   |               50.6292 |            5.99604 |                    -4.99615 |                     6.00011 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_0A069D33C5E5 | torus_2.4_final   |             2092.02   |            6.00151 |                    -5.00206 |                     6.00136 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_7AFEDA9B5A86 | torus_2.5_final   |               63.9989 |            5.99632 |                    -4.99642 |                     6.00012 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_54C84D7AE5C6 | torus_2.6_final   |             3367.59   |            6.00104 |                    -5.00144 |                     6.00092 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_815FBFFA77C1 | torus_2.7_final   |               78.2953 |            5.99701 |                    -4.99715 |                     6.00014 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_8D07A81DC11B | torus_2.8_final   |             1000.1    |            6.0007  |                    -5.001   |                     6.00062 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_DA8C4925D735 | torus_2.9_final   |               86.9181 |            5.99726 |                    -4.99742 |                     6.00017 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_FCB121101D97 | torus_3.3_final   |              533.972  |            5.99993 |                    -4.99998 |                     6.00005 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_DD20ED17B181 | torus_3.6_final   |              880.618  |            6.00033 |                    -5.00051 |                     6.00033 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_E02CE8D3915C | torus_3.9_final   |             1002.01   |            6.00079 |                    -5.0011  |                     6.00073 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_C4CB70901706 | torus_6.15_final  |             1007.1    |            6.00013 |                    -5.00026 |                     6.0002  | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_D89AA47313CD | torus_6.21_final  |             2746.24   |            6.00023 |                    -5.00038 |                     6.00019 | FAIL                | FAIL                        | PASS                   | FAIL      |
| K_D034F7BFAFEA | torus_6.9_final   |              933.391  |            6.00018 |                    -5.00032 |                     6.00025 | FAIL                | FAIL                        | PASS                   | FAIL      |

## Interpretation rules

- `monopole_1_over_r=FAIL`: the reconstructed closed-knot velocity tail does not produce the required $1/r$ potential through $\Phi=-v^2/2$.
- `pressure_poisson_monopole=FAIL`: the pressure-Poisson source integral does not approach the same non-zero monopole strength.
- `pressure_phi_closure=FAIL`: the Bernoulli/Beltrami identification $p/\rho_f\simeq-v^2/2$ is not supported in the far-field integral sense.
- Metric determinant and clock columns are algebraic/consistency diagnostics, not independent evidence.

## Blinding

Measurement is written under salted blind IDs. Source names are joined only during reveal. Thresholds are copied to `preregistered_config.json` before measurement.
