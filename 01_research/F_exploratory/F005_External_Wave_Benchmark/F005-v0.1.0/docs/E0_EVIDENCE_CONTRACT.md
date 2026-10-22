# E0 evidence contract

1. **Geometric evidence**: thesis Tables 1.1 and 2.1 set numeric dimensions and model constants; verified separately from any fit to sloshing frequencies. Source T75 flask uses soluble coffee, model water density; zero sigma is a declared modeling limit, not a measured surface tension.
2. **Physical coordinates**: define actual imposed longitudinal robot acceleration +x, physical right wall +x, positive water elevation up. Show where raw NPY indexing maps to those. Without independent mapping, set both signs `null`.
3. **Initial state**: require evidence for initial wave amplitudes and velocities for every run or a declared conditional-initialization protocol. Pre-motion mean subtraction alone is insufficient to certify rest.
4. **Independence**: geometry-only frequency/forcing from linear potential Euler; no ARX/oscillator values fitted to validation output. TRAIN-only sign diagnostic is explicitly observational; if used to assign relative sign it is a training calibration.
5. **Data safeguards**: frozen v0.4.3 split checked; don't index TEST/OOD response rows. Publication's 4-mode gravity-only approximation is source-based.
6. **Validity**: compare mode spacing, smallness of surface slope / wave height, effects of meniscus, wetting, liquid viscosity and residual energy separately. Linear inviscid zero-damping cannot reproduce experimental ringdown exactly.

## Formal equation

For signed conventions s_a and s_y each in {-1,+1}: eta_observed = s_y * eta_Euler[s_a * a_export], so in this linear model eta_observed = (s_a*s_y) * eta_Euler[a_export]. The four pairs reduce to two observationally distinguishable products.

## Reference

```latex
\bibitem{Camilotto2026}
D. Camilotto, ``A Comprehensive Data-Driven Framework for Robotic Liquid Sloshing Control: From Extensive Experimental Model Validation and Enhancement to Trajectory Optimization,'' Master's thesis, Politecnico di Milano (2026), \url{https://hdl.handle.net/10589/253216}.

\bibitem{Giulietti2026}
N. Giulietti, M. Bedodi, D. Ghavami, D. Camilotto, and H. Giberti, ``Robot-executed longitudinal sloshing dataset for rectangular tank liquid handling,'' Zenodo v1.0.0 (2026), \url{https://doi.org/10.5281/zenodo.20039757}.
```
