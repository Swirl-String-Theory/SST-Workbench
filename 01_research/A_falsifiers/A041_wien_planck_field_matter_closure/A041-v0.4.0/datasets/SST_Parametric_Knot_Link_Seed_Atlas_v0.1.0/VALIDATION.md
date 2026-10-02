# Validation — PKLSA v0.1.0

Overall: **PASS**

- 49 / 49 historical KnotPlot catalog families.
- 48 candidates per family; **2352 / 2352 unique candidate IDs**.
- 512 samples per component; all coordinates finite.
- PTSA trefoil population: 48 / 48.
- Generic SIAF branch: explicit global diffeomorphism; selected variants 0, 23 and 47 retain every multicomponent family’s nearest-integer pairwise linking signature.
- Historical KnotPlot pairwise-linking integer cross-check: **PASS for 24 multicomponent families**; signed orientation is ignored and absolute integer signatures are compared.
- Gilbert Fourier `A0/2` regression anchor L2a1: PASS, numerical |Lk|=1.000025.
- Torus analytic grid: `R > a > 0`, `b > 0` for all 48 parameter combinations; selected low/mid/high variants also retain linking integers, including the high-linking torus families.
- ZIP/package manifest integrity is checked separately by `tools/verify_atlas.py`.

The Gauss-linking audit uses 512-point component polylines and a midpoint discretization of the Gauss integral as an integer cross-check. For single-component knots no complete independent knot-invariant solver is bundled; their topology is inherited from the named source embedding through a global diffeomorphism. Hence PKLSA is a **constructive topology-preserving seed atlas**, not an independent topology-certification authority.
