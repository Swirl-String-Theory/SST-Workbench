# Gate-definities

Alle gates zijn standaard blockers. `NOT_RUN` is geen `PASS`.

## H0 — Input, discretization, and source-scale integrity

\[
\frac{\max_i \ell_i}{\min_i \ell_i}\le1.05.
\]

Wanneer de bron een gerapporteerde lengte en diameter bevat, geldt bovendien

\[
\frac{|L_{\rm sampled}-L_{\rm source}|}{L_{\rm source}}\le5\times10^{-3},
\qquad
\frac{|2\Delta_{\rm proxy}-D_{\rm source}|}{D_{\rm source}}\le3\times10^{-2}.
\]

Voor een bron zonder zulke metadata worden deze twee subtests als niet van toepassing behandeld.

## H1 — Two-branch contact-map extraction

- completeness \(\ge0.95\);
- RMS dubbel-kritische orthogonaliteitsresidu \(\le0.08\).

## H2 — Degree-one inverse contact branches

- beide windinggetallen zijn \(+1\);
- gecombineerde inverse-RMS \(\le0.01\).

## H3 — Paired primitive 9-billiard

Voor **beide** inverse contacttakken:

- closure \(\le2\times10^{-3}\);
- alle lagere perioden hebben residu \(\ge10^{-2}\);
- minstens negen afzonderlijke orbitpunten.

De circulaire Hausdorffafstand tussen beide orbitsets moet bovendien \(\le0.02\) zijn. Dit voorkomt dat alleen de numeriek gunstigste branch wordt geselecteerd.

## H4 — Carlen compatibility

- max van de \(\sigma\)- en \(\tau\)-compatibiliteitsresiduen \(\le0.20\);
- lokale vectorbalansresidu \(\le0.10\);
- ill-conditioned fractie \(\le0.05\).

Deze ruime standaarddrempel is een screeninggate. Publiceerbare claims vereisen een
resolutie-extrapolatie en een veel strenger foutbudget.

## H5 — Biot–Savart relative equilibrium

Voor minstens één full-kernel core ratio:

\[
\varepsilon_{\rm RE}\le0.25.
\]

## H6 — Hamiltonian gradient and emergent tension

Voor minstens één full-kernel core ratio:

- force-shape residual \(\le0.35\);
- alignment cosine met \(-\kappa\mathbf n\) \(\ge0.50\);
- fitted global scale is positief;
- tension CV \(\le0.50\);
- binormal leakage \(\le0.25\).

## H7 — Finite-core robustness

De gezamenlijke H5/H6-passfractie over de full-kernel core sweep moet

\[
f_{\rm pass}\ge0.60
\]

zijn. Eén geselecteerde corewaarde is dus onvoldoende.

## H8 — Nonlocal guard

Voor minstens één nonlocal-kernel core ratio:

- shape residual \(\le0.50\);
- alignment cosine \(\ge0.50\).

De uitkomst moet opnieuw worden getest bij veranderend sampleaantal en `local_band`.

## Eindverdict

- ten minste één `FAIL`:
  `FALSIFIED_OR_UNRESOLVED_AT_ONE_OR_MORE_GATES`;
- geen `FAIL`, maar minstens één `NOT_RUN`:
  `INCOMPLETE_REQUIRED_GATES_NOT_RUN`;
- alle blockers `PASS`:
  `NOT_FALSIFIED_BY_CONFIGURED_GATES`.

De laatste status is geen bewijs; het is alleen een niet-verwerping binnen het huidige
model- en foutbudget.
