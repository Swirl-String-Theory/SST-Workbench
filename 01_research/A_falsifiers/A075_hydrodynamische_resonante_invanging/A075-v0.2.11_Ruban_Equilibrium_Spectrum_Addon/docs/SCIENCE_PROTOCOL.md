# A075 v0.2.11: mathematische contracten, falsifiers en stopcriteria

## Filamentmodel

Nondimensionale referentie R0=1, Gamma=2*pi, delta=0.05,
Lambda=(7/5)+(1/2)*ln(200), tildeLambda0=(7/5)-(1/2)*ln2.

De volledige continuümvergelijking gebruikt de geregulariseerde filamentinteractie

`F[X](theta) = (Gamma/4pi) int X'(phi) cross (X(theta)-X(phi))/(|X(theta)-X(phi)|^2+delta^2)^(3/2) dphi + (Gamma*tildeLambda0/4pi) X' cross X'' / |X'|^3`.

Voor Gamma=2*pi zijn de twee coëfficiënten respectievelijk 1/2 en tildeLambda0/2. Delta is een filamentregularisator, niet de Gauss-core sigma in A075 Euler3D. R0, Gamma en de modeltijd zijn dimensieloos genormaliseerd; alle geprojecteerde residuen worden gedeeld door Gamma bij R0=1.

## Relatief-evenwicht

`Pperp(F[X] - U ez - Omega ez cross X) = 0`.

Het kleinste-kwadratenprobleem fit U en Omega, waarna radiale en z-Fouriercorrecties worden geoptimaliseerd. Het optimizersucces, een dalend residu, minimale energie of booglengte zijn **geen** bewijs voor een exact evenwicht.

## Mathematisch discrete linearisatie

Voor een exact relatief evenwicht, laat `alpha(theta) = ((F-U ez-Omega ez cross X) dot X')/|X'|^2` de tangentiële gauge-snelheid zijn. De gelineariseerde operator in een vaste lokale normaalframe is

`J deltaX = Pnormal(DF[X] deltaX - Omega ez cross deltaX - alpha(theta) d(deltaX)/dtheta)`.

Deze linearisatie is geldig bij een *echte* relatief-evenwichtsvorm. Voor een niet-stationaire referentie is de berekende matrix **alleen** een instantane discrete gevoeligheidsmatrix, geen lineaire stabiliteitsoperator rond een oplossing. De formele volledige matrix bevat 2N kolommen, geen truncatie naar een beperkte Fourier-Ritz-ruimte. Tangent-, translatiesymmetrie-, rotatiesymmetrie- en mogelijke parametrisatie-nulmoden moeten later onafhankelijk gekwalificeerd worden.

## Gates

- `SOURCE`: A007 2048_xyz hash en originele A075 Eq.9 bronhash exact gelijk; mismatch=STOP.
- `NUMERICAL_OPERATOR`: onafhankelijke midpoint/trapezium-vormen, FD-stap h tegen h/2; incongruentie=UNRESOLVED.
- `GEO_RES`: maximale segmentlengte/delta <0.25 wordt als een *voorgestelde screen* gemeten. Geen fysische sufficiëntieclaim.
- `RE_CANDIDATE`: eps<=1e-5 als *voorgestelde screendrempel*, plus ten minste drie onafhankelijke ruimtelijke niveaus, meerdere shape-basisordes, topologische en quadratuurvalidatie. Zelfs dan wordt geen exact bewijs geclaimd.
- `SPECTRUM`: 2N eigenwaarden berekend=een COMPLETE FINITE-N MATRIX; voor fysische stabiliteitsinterpretatie moeten exact RE, spectrale convergentie (laagfrequente eigenparen), gauge-normalisatie en kernresolutie onafhankelijk slagen.
- `EULER`: A075 3D finite-core, periodieke box, vloeistofvolumemesh, momentum, heliciteit, behoud en topologie zijn NOT_RUN.
- `FRAMEWORK`: geen FREEZE/BASIC/FULL; alle A075 G-gates blijven ongewijzigd.

## Numeriek inzicht en falsifieerbaarheid

Indien de residuwaarde bij hogere N naar een strikt positieve waarde blijft convergeren, is de onderzochte beperkte shape-ansatz niet exact relatief-stationair voor de gebruikte modelparameters. Dit kan niet worden uitgebreid tot uitspraken over alle mogelijke torusachtige vormen, alle perturbaties of volledige driedimensionale SST-stabiliteit.

De beste volgende stap is een vrije normale-shape Newton-Krylov-methode, met arclength-gauge, numerieke nulmoden en viriale/invariant-constraints, gevolgd door quadratuur- en basisconvergentie. Pas daarna volledige spectrale interpretatie.

## Referenties, copy-ready LaTeX

```latex
\begin{thebibliography}{9}
\bibitem{Ruban2018}
V. P. Ruban (2018),
``Long-lived quantum vortex knots,''
JETP Letters 107, 307--311.
DOI: 10.1134/S0021364018050120.
\bibitem{Ruban2018Quasistable}
V. P. Ruban (2018),
``Quasi-stable configurations of torus vortex knots and links,''
Journal of Experimental and Theoretical Physics 127, 581--586.
DOI: 10.1134/S106377611809008X.
\bibitem{Boyd2001}
J. P. Boyd (2001),
Chebyshev and Fourier Spectral Methods, Second Edition,
Dover Publications.
ISBN: 9780486411835.
\end{thebibliography}
```
