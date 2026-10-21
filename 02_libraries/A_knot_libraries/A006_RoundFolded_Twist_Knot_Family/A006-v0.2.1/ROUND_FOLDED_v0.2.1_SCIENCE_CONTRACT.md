# Science contract — TikZ round-folded reference cases

## User-supplied planar source

Fourteen ordered 2D control points for 5_2 and 6_1, one closed `\strand`, TikZ `use Hobby shortcut`. v0.2.1 preserves this control polygon but uses periodic cubic-spline interpolation as a surrogate pending direct Hobby extraction. Topologically, no projection of a closed curve is a knot embedding until over/under data are specified.

Let the closed interpolation be `r(u) = (x(u),y(u))`, with `u ∈ R/Z`. For each **transverse** self-crossing solve `r(u_j) = r(v_j)` with `u_j != v_j`. For alternating knots assign the sorted encounter sequence `O,U,O,U,...`. A smooth lift is

\[
 X(u) = (x(u), y(u), z(u)), \qquad z(u)=H\sum_{j=1}^{2n} \varepsilon_j \exp[-d_{S^1}(u,u_j)^2/(2w^2)],
\]

where `H=0.10`, `w=0.011`, `epsilon_j=+1` for over and `−1` for under encounters, and `d_{S^1}` is the shortest distance on the unit parameter circle. Every crossing gets an explicit nonzero height difference; independent 3D segment clearance is tested after uniform 3D arclength discretization.

**No `r_c` physical core radius is assigned.** `R` and all other lengths are arbitrary dimensionless KnotPlot coordinates. Distinguish `knot clasp radius` from canonical SST `r_c`.

## Gates

G0 source control vertices and SHA256 provenance; G1 a closed smooth one-component curve; G2 exact crossing count 5/6; G3 Fox Alexander 2t²−3t+2 and 2t²−5t+2 (up to units) and det 7/9; G4 positive 3D projection lift; G5 discrete 3D segment clearance; G6 KPT LOCD byte-identical roundtrip. These static gates are executed by the included tests/build. G7 original compiled Hobby equivalence remains UNRESOLVED; G8 KnotPlot roundtrip and completed-`go` status NOT TESTED; G9 topological stability under numerical steps UNRESOLVED; G10 Borromean decorated 5_2,5_2,6_1 and Milnor μ̄123 NOT IMPLEMENTED; G11 3D Euler/finite-core NOT TESTED.

## References

```latex
\bibitem{Alexander1928} J. W. Alexander (1928),
``Topological Invariants of Knots and Links,''
Transactions of the American Mathematical Society 30, 275--306.
https://doi.org/10.1090/S0002-9947-1928-1501429-1.

\bibitem{Hobby1986} J. D. Hobby (1986),
``Smooth, Easy to Compute Interpolating Splines,''
Stanford University Report STAN-CS-86-1099.
https://i.stanford.edu/pub/cstr/reports/cs/tr/86/1099/CS-TR-86-1099.pdf.

\bibitem{SchareinKnotPlot} R. G. Scharein,
``KnotPlot Manual,'' Hypnagogic Software, https://knotplot.com/manual/.
```
