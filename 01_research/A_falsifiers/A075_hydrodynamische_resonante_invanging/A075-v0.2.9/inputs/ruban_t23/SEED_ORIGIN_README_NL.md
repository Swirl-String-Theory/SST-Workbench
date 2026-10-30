# Ruban T(2,3) seed v0.1.0 — exact-paper-parameter reconstruction

**Status:** analytisch geconstrueerde kandidaat; niet Rubans oorspronkelijke discretisatie en niet dynamisch gevalideerd. De wetenschappelijke bron is V. P. Ruban, *Long-lived quantum vortex knots* (2018), figuur 3, pagina 3; daarnaast vergelijkingen (8) en (9) op pagina 2.

## 1. Originele papierparameters (geen schatting uit pixels)

| Grootheid | Exacte vastlegging | Dubbelprecisie-evaluatie |
| --- | --- | --- |
| R0 | 1 (dimensieloos) | 1 |
| B0 = r0/R0 | 77/500 | 0.154 |
| r0 | 77/500 | 0.154 |
| delta | 1/20 | 0.05 |
| delta² | 1/400 | 0.0025 |
| Lambda | 7/5 + ln(200)/2 | 4.049158683274018... |
| xi/R0 (uit Lambda) | exp(-7/5)/sqrt(200) | 0.01743703854231245... |
| Lambda-tilde0 | 7/5 - ln(2)/2 | 1.053426409720027... |
| Coëfficiënt lokale inductie in Rubans vgl. (9) | Lambda-tilde0/2 | 0.5267132048600136... |
| Circulatie | 2*pi | Ruban-model (dimensieloos) |

**Belangrijk:** Rubans delta is de *filament-regularisatie* in de Biot–Savart-kernel; xi is de afgeleide effectieve kernparameter. delta en xi zijn niet gelijk. Zijn vergelijking (8) is

    Lambda = ln(R0 / xi) = ln(R0 / delta) + Lambda_tilde0.

De Gaussische finite-core-vorticiteitsbreedte van de **3D periodieke Euler-oplosser** A075 is een ander modelobject. `cfg.core=0.05` overnemen is **geen** wetenschappelijk gerechtvaardigde modeloverzetting.

Rubans figuur 3 toont dit voorbeeld bij t=320, terwijl het artikel ook levensduren boven 300 modeltijdseenheden bespreekt. Dat is geen bewijs dat de combinatie wereldwijd optimaal is, en t=320 is niet zonder schalingsafleiding gelijk aan 320 s A075-tijd.

## 2. Exacte analytische torusgeometrie

Neem theta in [0,2*pi), p=2 toroidale windingen en q=3 poloïdale windingen; deze conventie komt overeen met A075's bestaande analytische trefoil-formule:

    x(theta) = (1 + (77/500) cos(3 theta)) cos(2 theta)
    y(theta) = (1 + (77/500) cos(3 theta)) sin(2 theta)
    z(theta) = (77/500) sin(3 theta).

Alle waarden zijn gedefinieerd zonder afronden naar hele stralen. Het discrete XYZ-formaat bewaart 17 significante cijfers per coördinaat. Iedere XYZ-regel bevat exact drie float64-getallen; eventuele `#`-commentaarregels zijn leesbaar door `numpy.loadtxt`.

Ruban schrijft **'slightly perturbed trefoil knot'** maar publiceert geen volledige vertices/stoormodus of random seed. Wij leveren de **onverstoorde** exacte geometrische uitgangsseed. De levensduur uit figuur 3 kan dus NIET als verwachte prestatie van deze seed worden aangemerkt.

## 3. Inhoud

- `seeds/RUBAN_T23_B0_0p154_N2048_EQUAL_ARCLENGTH.xyz`: **primaire testseed**, 2048 punten, gelijkmatig over de analytische booglengte verdeeld.
- `seeds/RUBAN_T23_B0_0p154_N4096_EQUAL_ARCLENGTH.xyz`: geometrische discretisatiecontrole bij 4096 punten.
- `seeds/RUBAN_T23_B0_0p154_N2048_UNIFORM_THETA.xyz`: controle voor het effect van gelijke theta-stappen (in plaats van gelijke booglengte).
- `generate_seed.py`: reproduceerbare formule-generator; bestaande bestanden worden standaard niet overschreven.
- `verify_seed.py`: onafhankelijk lezen, hashes, de torusvergelijking, windingen en segmentverdeling controleren.
- `SEED_MANIFEST.json`: alle exacte parameters, gereconstrueerde vertexmetingen, herkomst en bestandshashes.
- `PARAMETER_SCAN_PROPOSAL.json`: **niet-paper** onderzoekspunten om de lokale gevoeligheid rond 0.154 later te bepalen.

## 4. Gebruik

    python verify_seed.py

Voor nieuwe output (zonder bestaande files te wijzigen):

    python generate_seed.py --out MY_NEW_SEEDS

Gebruik `--force` alleen voor expliciet opnieuw genereren op een reeds bestaande locatie. Byte-identieke hashes van berekende trigonometrische waarden zijn niet over platformen gegarandeerd: vergelijk numerieke validatie en bewaar het geleverde ZIP als onveranderlijke bron.

## 5. A075 — integratie en veiligheidsgrenzen

A075-v0.2.7 heeft **nog geen** `ruban_t23`-geometrie-branch: `--knots 3_1` kiest de standaardtrefoil met B0=0.32, **niet** deze seed. Eerst in een **nieuwe A075-falsifierversie**, met eigen bron- en protocolmanifest, een expliciete `ruban_t23`-loader opnemen. De bestaande versies en hun FREEZE moeten intact blijven.

Bij een uniform isotroop schalen met factor s blijven windingen en B0 gelijk, terwijl R0, r0 en delta **allemaal** met factor s moeten worden omgezet voor de *Ruban-filamentvergelijking*. De referentieseed heeft R0=1 in dimensieloze units. In de huidige A075-overlappende ontvanger/donor-opzet wordt een tweede trefoil standaard geschaald naar maximaal 0.82 xy-radius; dat correspondeert met s=0.82/1.154, niet met R0=1.

Een 80^3 rooster in een periodieke doos L=10 heeft dx=0.125. De Ruban-regulator delta=0.05 zou daar slechts 0.4 roosterstap zijn bij R0=1 (na de bestaande A075-schaal nog minder). Behandel delta dus niet als een resolvabele Euler-Gauss-core. Voor een afzonderlijke 3D-Eulerbeoordeling zijn een expliciete gladde kern, onafhankelijke kern-, ruimte-, tijd- en domeinconvergentie nodig. Periodieke beelden kunnen resultaten beïnvloeden.

**Aanbevolen testvolgorde:** (1) geometrie en hash; (2) Ruban-filamentdynamica met identieke regularisatie en lokale-inductieterm, onder gedocumenteerde perturbaties; (3) onafhankelijke tests van parametervariatie en tijd-/vertexconvergentie; (4) A075-veldtest met correct geadmitteerde geometrie en fysieke resolutie; (5) pas daarna donor-energie-invanging.

## 6. 'Beste' punt versus echte optimalisatie

B0=0.154, delta=1/20 is een **gedocumenteerde langlevende casus**, niet de exacte optimumlocatie. De inverse-lifetimegrafiek heeft meerdere vensters en de lange trajecten werden bij een bovengrens afgebroken. De originele outputwaarden zijn niet in de PDF gegeven. Een scherper optimaal B0 moet uit onafhankelijke herhaalbare solverberekeningen blijken en mag niet uit figuurpixels worden gegokt. `PARAMETER_SCAN_PROPOSAL.json` is daarom bewust als nieuw testplan gelabeld.

### Alleen-lezen importfunctie voor latere A075-integratie

`a075_seed_loader.py` bevat `load_ruban_t23(seed_package_root, n=2048, target_outer_radius=0.82, center_z=0.65)` en geeft `(points, provenance)` terug. De functie controleert de bronhash, behoudt B0 bij schaling en verandert geen A075-projectbestanden. De bijbehorende `RUBAN_FILAMENT_CONFIG.json` bevat de Ruban-vergelijking-(9)-parameters als expliciete `float64`-velden en de exacte symbolische waarden.

**Niet vergeten:** A075-v0.2.7's huidige `curve('3_1', ...)` maakt zelf de geometrie met B0=0.32 en gebruikt standaard slechts 192 geometriepunten. Om Rubans seed echt te testen is dus een nieuwe expliciet geversioneerde A075-geometriebranch nodig, die `points` met voldoende oorspronkelijke resolutie doorgeeft en de bronhash registreert. Deze seed-release past A075 zelf niet aan.
