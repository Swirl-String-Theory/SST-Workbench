# C006 v0.3.0 preliminary conclusions

These statements refer to the bundled quick complete fallback run and the independent full Phase-V fallback run. They are not native production-certification results.

- **K15 = WARN.** The generic QEP implementation self-test passes, but the current trefoil projected Kelvin spectrum is not fully persistent under the pre-registered \(N=24,32,40\) ladder at the 0.20 relative-shift threshold. This is evidence against treating the present low-resolution frozen spectrum as converged.
- **K16 = DIAGNOSTIC.** The \(\varepsilon/D\in\{0.08,0.10,0.12\}\) scan shows one real-part branch turning for \(m=1\). The descriptive non-oscillatory census is zero for \(m=1,2\) and appears for one \(m=3\) mode at the two larger regularizations. This is not interpreted as viscosity.
- **K17 = DIAGNOSTIC.** The projected spectra show large conjugate/quartet closure defects in this four-state basis. Because the projection need not preserve the full Hamiltonian structure, this does not by itself falsify conservative SST dynamics.
- **K18 = PASS for implementation self-test, but all SST sector pretests fail.** The common/differential off-block coupling ratio is about 0.97 in each tested \(m=1,2,3\) case, far above the frozen 0.05 eligibility threshold. Therefore the present projected basis does not support treating common and differential sectors as approximately independent Darboux partners.
- **K19 = SKIP.** No SST-derived scalar second-order operator pair exists in this package; no physical Darboux-isospectrality claim is made.
- **K20 = SKIP** in the standalone Phase-V validation because the K6 true-Floquet prerequisite was not supplied/opened.

The scientifically useful outcome is therefore negative/disciplining rather than confirmatory: v0.3.0 exposes that the present projected trefoil spectrum needs stronger resolution certification, and that the obvious common/differential block split is not presently a viable Darboux-pair candidate.


## Full-preset confirmation

The full Phase-V ladder did not change the qualitative conclusion. K15 remained `WARN`: no tested mode \(m=1,\ldots,5\) had all four projected eigenvalue branches persistent at the frozen 0.12 per-step threshold. K18's synthetic Darboux implementation continued to pass, while every physical common/differential matrix pretest failed; the off-block coupling ratios remained near unity (about 0.968–0.981). Thus the current basis split is strongly coupled rather than an approximately decoupled partner pair.
