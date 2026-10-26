# Universal Borromean Builder · VortexLab v0.1.0

**Status: GEOMETRIC_CANDIDATE / DEVELOPMENT. Geen Euler-stabiliteit of topologische certificatie.**

Deze additieve module gebruikt drie onafhankelijke selecties uit de *werkelijk aanwezige* VortexLab-catalogi:

- `Gilbert Ideal/Tight` (`ideal_knots_data.js`)
- `Fourier-series` (`fourier_knots_data.js`)
- `KnotPlot` (`knotplot_knots_data.js`)
- `A006 Twist/Torus` (`twist_knot_data.js`)

Alleen **knoopbronnen met exact één component** worden als invoer getoond. De in dit snapshot gevonden 222 catalogusitems zijn niet 222 bewezen verschillende knooptypen. Een ontbrekende of ongeschikte bron wordt niet geïmproviseerd. Bronidentiteit blijft ongetoetst.

## Installatie (Windows)

Pak deze ZIP uit **buiten** de bestaande VortexLab-map. Gebruik Python 3 en voer uit:

```powershell
py -3 .\install.py --root "C:\workspace\projects\SST-Workbench\05_apps\A003_vortexlab" --check
py -3 .\install.py --root "C:\workspace\projects\SST-Workbench\05_apps\A003_vortexlab" --apply
```

De installer controleert of de modulaire app (`apps/web`) en alle vier catalogi bestaan. Hij kopieert alleen vier eigen bestanden, voegt een navigatielink aan `apps/web/index.html` en `apps/web/catalog.html` toe, en bewaart `.pre-universal-borromean-v0.1.0.bak`-kopieën van de gewijzigde pagina's. Afwijkende al bestaande extensiebestanden worden geweigerd. Er worden geen bestaande catalogi, Euler-solvers, knoop-seeds of resultaten gewijzigd.

Open **`apps/web/borromean.html`**, of open VortexLab en kies *Borromean Builder* in de bovenbalk. De bestaande `apps/web/vendor/three.min.js` wordt gebruikt; geen aparte installatie van modules vereist.

## Gebruik

1. Selecteer onafhankelijk bron en knoop voor **A**, **B** en **C**.
2. Kies de bronresolutie (`N=256`, `384` of `512`) en de relatieve grootte van de toegevoegde knoop.
3. Klik **Genereer geometrie en controleer**.
4. Draai de 3D-preview met de muis en beoordeel de numerieke gates.
5. Exporteer een 3-blokken-`XYZ`-bestand en een `JSON`-manifest. Import in VortexLab kan via de bestaande session-XYZ-importer. De geometrie wordt niet automatisch als fysisch gelijkwicht gestart.

Voorbeelden: `3_1 / 3_1 / 3_1`, `3_1 / 5_1 / 7_1`, of een menging uit ideal, Fourier en KnotPlot. Onder `examples/` staan daadwerkelijk gegenereerde testseeds, elk met apart manifest. **Een PASS bij alle statische numerieke gates is geen bewijs van correcte knoopidentiteit.**

## Constructie

Neem de driecomponentige Gilbert-embedding `L6a4` als Borromeaanse drager `B`. Selecteer voor iedere component een gesloten knoopcurve `K_i` en vervang een korte boog door een verkleinde lokaal geknoopte streng, met twee verbindingssegmenten. Dit implementeert geometrisch de beoogde lokale verbonden som

\[
 L \sim B \#_1 K_1 \#_2 K_2 \#_3 K_3.
\]

Een **zuivere topologische verbonden som binnen een geïsoleerde bol** behoudt de Borromeaanse globale verstrengelingsstructuur, maar de huidige numerieke centerlines hebben **nog geen algemeen isotopiebewijs of Milnor-invariant-certificaat**. Strikt Brunniaans is deze link niet zodra de componenten zelf niet-triviaal geknoopt zijn. Noem hem *decorated Borromean-pattern link* tot verdere kwalificatie.

Gauss' paargewijze linking-getal

\[
 \operatorname{Lk}(C_i,C_j) = \frac{1}{4\pi}
 \oint_{C_i}\!\oint_{C_j}
 \frac{(d\mathbf r_i\times d\mathbf r_j)\cdot(\mathbf r_i-\mathbf r_j)}{\lVert\mathbf r_i-\mathbf r_j\rVert^3}
\]

wordt hier **numeriek benaderd met segmentmiddelpunt-kwadratuur**. Het is geen robuust integraalcertificaat voor elke zeer nabije curve of zeer lage resolutie.

## Gates en beperkingen

| Gate | Implementatie | Interpretatie |
|---|---|---|
| Drie polygonale gesloten componenten | JA | Periodieke indexering, positieve segmentlengten |
| Numerieke bronkwaliteit | JA | Geen NaN/Inf, degeneratie en sterke segment-uitschieters |
| Niet-aangrenzende zelfafstand | JA | Eenvoudige segment-tot-segment-ondergrens |
| Intercomponent afstand | JA | Positieve scheiding van de polygonale centerlines |
| Paargewijze `Lk` | JA | Segmentmiddelpuntbenadering nabij basiswaarden |
| Afzonderlijke knoopidentiteit | **NIET bewezen** | Vereist onafhankelijk isotopie-/knooppolynoomcertificaat |
| \(\overline\mu_{123}\) | **NIET berekend** | Vereist Milnor-certificering met local-knot normalisatie |
| Continue kromming, finite-core reach | **NIET berekend** | Geen minimum toegestane kernradius gecertificeerd |
| Volledige Euler-dynamica | **NIET gedraaid** | Niet gelijkstellen aan stabiele vortexseed |

**Let op A006:** oudere twist-seeds zijn in eerdere tests foutief als dubbelgevouwen C-vormen aangetroffen. Selectie is mogelijk, maar de Builder kan hun werkelijke topologische identiteit **niet** zelfstandig certificeren. Gebruik ideal/Fourier/KnotPlot voor de eerste gecontroleerde suites en keur A006 per knoop afzonderlijk goed.

De geometrische coördinaten zijn catalogus-/genormaliseerde eenheden, **niet direct meters**. Er wordt geen circulatie \(\Gamma\), finite-core radius of materiaaleigenschap aan toegekend. Voor een Euler-falsifier zijn nog ruimtelijke/tijdconvergentie, remeshingkwalificatie, topologiebehoud en conserveringstests nodig.

## Regressietests

Met Node.js (JavaScript-runtime) in een lokale developmentomgeving en `VL_SOURCE` gericht naar de bestaande map `apps/web`:

```powershell
$env:VL_SOURCE="C:\workspace\projects\SST-Workbench\05_apps\A003_vortexlab\apps\web"
node .\tests\test_builder.cjs
node .\tests\sample_export.cjs
```

De testen laden de *bestaande* gegevens, controleren alle drie de componenten en verifiëren `3_1/3_1/3_1`, `3_1/5_1/7_1`, een gemengde cataloguscombinatie en een numeriek foutieve invoer. Hun resultaat is statisch, geen topologische of fysische certificatie. Browser/WebGL-weergave wordt hier niet als geautomatiseerd getest geclaimd.

### Bronnen (LaTeX)

```latex
\bibitem{Milnor1954}
J. Milnor (1954), Link Groups,
Annals of Mathematics 59, 177--195.
https://doi.org/10.2307/1969832

\bibitem{Rolfsen1976}
D. Rolfsen (1976), Knots and Links,
Publish or Perish, Berkeley.
ISBN 978-0-914098-16-4.

\bibitem{Gauss1833}
C. F. Gauss (1833), Integrals for linking numbers,
in his mathematical manuscripts; see Rolfsen (1976)
for the modern Gauss linking integral.
```
