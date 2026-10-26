# A003 TwistKnot Flow Lab — P6a voorgeschreven achtergrondbundel (overlay)

**Status:** UI-integratie voor bestaande grofkorrelige bundelprovider / RESEARCH-TRACK / **NIET** fysisch gevalideerde tweewegsfilamentdynamica.
**Bron:** actuele A003 `apps/web/twist-flow/` uit Google Drive, gelezen op 26 oktober 2026. Bestaande runtime blijft byte-voor-byte onveranderd.

## Wat is toegevoegd

Nieuwe sectie `03 / PARALLELLE ACHTERGRONDKERNEN`, met drie standen:

- **Uit**: bestaande geïsoleerde-knoopreferentie, default.
- **Grofkorrelig bundelveld**: stelt via bestaande native controls `cSSTBundle`, `cBundleFlow`, `cBundleBEM` (`false`) een parallel analytisch achtergrondveld in. Dit beïnvloedt de dynamische knoop en tracers, maar niet via zelfstandige achtergrondfilamenten.
- **Grofkorrelig + statische buisrandcorrectie**: schakelt daarnaast bestaande BEM (Boundary Element Method / randelementenmethode) in. De schijnbaar gebogen lijnen komen uit een statische/vastgelegde vorticiteitscorrectie om een uitsluitingsbuis, niet uit advectie van onafhankelijke vortexkernen.

Bediening: opgelegde hoeksnelheid `Ω` in s⁻¹ en aantal **getekende** bundellijnen; beide hebben expliciete eenheden/betekenis. Modewissels resetten de simulatie **niet automatisch**; stop, reset en reproduceer bij modelvergelijkingen.

De UI initialiseert de bestaande controls expliciet UIT; dit wijzigt geen bestaande numerieke kernel, geometrie of circulatie. Bij wisselen naar vrije demo-Γ wordt de bundel uitgeschakeld, om de onderzoeksmodus niet stilzwijgend te mengen met een bewegingsdemo.

## Installatie

1. Maak een back-up van de bestaande `A003_vortexlab/` map (de bestaande P5-baseline behouden).
2. Kopieer de drie overlaybestanden uit `apps/web/twist-flow/` naar dezelfde relatieve locatie in de bestaande A003-root.
3. Run vanuit `A003_vortexlab/`: `npm run check` en `npm start`.
4. Open `http://127.0.0.1:4173/twist-flow/`. Kies 'Grofkorrelig bundelveld' of '...BEM'; controleer de native readout in de nieuwe sectie.
5. Als BEM `niet actief` rapporteert, interpreteer de lijnen niet als geldige buitencorrectie; bekijk numerieke kernstraal en resolutievloer.

**NIET** de bestanden in `apps/web/src/legacy/` vervangen. Niet op willekeurige oudere runtimeversies toepassen.

## Beperkingen (niet weg te redeneren)

1. `bundleVelocityProfileAt()` is een voorgeschreven, gemiddeld veld; het rooster van getekende lijnen bestaat **niet** als terugwerkende discrete vortexfilamenten.
2. `traceBundleVorticityLine()` integreert richting van een (eventueel BEM-gecorrigeerd) instantaan vorticiteitsproxyveld; het integreert geen materiële vortexkernbanen in de tijd.
3. In de huidige bron berekent de BEM afzonderlijke gradientcorrecties voor `u` en `ω`. Voor de getoonde correctie geldt daarom niet automatisch `ω = ∇×u`. De BEM-weergave moet een aparte consistentie/falsificatiegate krijgen, voordat dit als werkelijke afbuiging wordt aangemerkt.
4. Het opleggen van geen normale doorstroming op een quasi-statische *knooptube* lijkt op een rigide uitsluitingsgrens. Een vrije, materiële vortexbuis heeft geen starre wand en vereist gezamenlijke tijdsevolutie.
5. De bundel Ω=1 s⁻¹ is de bestaande softwaredefault, **geen** SST-gevalideerde kosmologische of microscopische dichtheidswaarde. De getekende lijnentelling is niet gelijk aan het fysische filamentaantal.
6. P6a laat bestaande Biot–Savart–LIA-, regularisatie-, CFL-, contact- en topologiegates intact.

## P6b vereist, voor echte fysieke vortexachtergrond

Maak M onafhankelijke filamenten met elk `X_j(s,t)`, `Γ_j`, `a_j(t,s)`, lange of periodiek doorlopende z-voorwaarden en mutuele Biot–Savart-interacties op alle knoop- en achtergrondpunten in één RK4-integratiestap. Voer daarna circulatie- en vorticiteitsconsistentie, materiaalbehoud, kernvolume, contact/reconnection guards, heliciteit (waar geldig), spatiotemporele convergentie en nul-bundel-pariteit uit. Een numerieke regularisatie `a_sim` is geen fysieke finite-core-sluiting. Voor de eerste fysische testrun: één ring + 1 rechte achtergrondkern, daarna trefoil 3_1 + kleine parallelle bundel en pas daarna gekwalificeerde 5_2 / 6_1-geometrieën. Geen fysische claims vóór die gates.

## Bronhashes (vóór overlay)

```
apps/web/twist-flow/index.html       e888f8b0747d3803676e7044aea1cbbd3347b48dabbc785d73b5c722df249cee
apps/web/twist-flow/twist-flow.js    22ecd8d0a0c6a9da60985ec0e5be371c38ae9f960479393144838c2678c4d449
apps/web/twist-flow/twist-flow.css   aa45c59c383ac3664d6baf2e1c800ef95c9ad7f60971e03418103c7928396b03
apps/web/src/legacy/vortexlab-runtime.js
                                    fe37d9bd619dfe38ce41b4fe96c79a44f15d63bf041bd4c5f55a5763507c237c
```

**Tests in deze omgeving:** JavaScript parse (`node --check`) en statische UI/API-contractcheck. `npm run check` en echte browserintegratie moeten op de volledige lokale A003-installatie worden uitgevoerd. Deze overlay is **niet** in Google Drive teruggeschreven.
