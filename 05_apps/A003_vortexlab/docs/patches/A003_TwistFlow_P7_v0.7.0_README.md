# A003 TwistKnot Flow Lab — P7 v0.7.0

**Patchnaam:** `A003-TwistFlow-P7-IdealReferenceMaterialStretch-v0.7.0`  
**Bron:** exact door gebruiker bijgevoegde `A003_vortexlab(2).zip`, op 26 oktober 2026.  
**Basisruntime:** VortexLab 7.6.25b-M1 + P6 Tube/Probe/Motion + P6a achtergrondbundel.  
**Status:** engineering patch; mathematisch consistent **geometrisch meetmodel** / RESEARCH-TRACK; **geen fysisch gecertificeerde finite-core-solver**.

## Nieuwe Model A-regel

Alleen `ideal` Gilbert-ideal/tight **enkelvoudige** gesloten knopen met metadata `ideal=true`, `L>0`, `D>0` en exact één component mogen een materiële referentie starten. `KnotPlot`, `twist/A006`, links, auto-relax en `N192`-preview zijn uitgesloten van Model A. Zij blijven bruikbaar in de overige VortexLab-modi.

Bij een daadwerkelijke `resetState()` met een geschikte knoop geldt als *hypothese* `a_K(0)=r_c=1.40897017e-15 m` en `L_phys(0)=2*r_c*(L/D)_Gilbert`. De originele centerline wordt **niet** fysisch naar femtometers gedwongen in de bestaande centimeter-georiënteerde solver. In plaats daarvan wordt exact één vaste dimensieloze schaalfactor `s_phys = L_phys(0)/L_sim(0)` vastgelegd. Zo wordt het oorspronkelijke `R0=0.07 m` niet abusievelijk als fysieke omvang gerapporteerd.

Na **iedere werkelijk geaccepteerde** solvertijdstap, en pas ná de contact/rollback-gates:

- `lambda_global(t)=L_sim(t)/L_sim(0)`; `a_equiv(t)=r_c / sqrt(lambda_global(t))`.
- Materiële segmenten behouden hun indexlabel. `lambda_i=ell_i(t)/ell_i(0)`; `a_i(t)=r_c / sqrt(lambda_i)`.
- De ruimtelijke centerline-uitgestrektheid volgt uit de werkelijk geëvolueerde geometrie: `R_xy(t)=max hypot(x_i-xbar, y_i-ybar)*s_phys`. Dit is **niet** gelijkgesteld aan de kernstraal.
- `V_ref = pi*r_c^2*L_phys(0)`. De getoonde `volumeRelativeError` is een **algebraïsche controle van de opgelegde lokaal-volumebehoudende reconstructie**, geen onafhankelijke meting of numeriek Euler-behoudsresultaat.
- Een uniforme verdubbeling van de segmentlengte halveert het buisoppervlak en verkleint de radius met `1/sqrt(2)`. Translatie wijzigt de gemeten `lambda` niet.

### Belangrijk wetenschappelijk onderscheid

`a_i(t)` is een *post-processed equivalente materiële kernstraal*. De bestaande `P.a` (`a_sim`: numerieke Biot–Savart-regularisatie), zichtbare tube, topology/contact-guards, circulatie, tijdintegrator en dynamica zijn **ongewijzigd**. Het resultaat bepaalt dus **niet** een zelfconsistent evoluerende finite-core-Euler-knoop, en mag niet worden gebruikt als fysisch bewezen absolute knoopgrootte, stabiliteit, stationair evenwicht of knoopisotopie.

De oorspronkelijke Gilbert-Fourierparameters en geometrieën worden niet aangepast. Een ideal-relaxed referentiebestand is géén dynamisch relaxte Euler-oplossing. De gekozen canonieke `r_c` is hier een expliciete hypothese over de materiaalbuisstraal, zelfs al heeft de bestaande runtime `rCorePhysical=null` en benoemt zij deze constante intern als `R_HORN_SST`.

De interne simulatie-`tPhys` blijft ongewijzigd en mag zonder onafhankelijke dynamische similariteitskwalificatie niet met fysieke femtoseconden worden gelijkgesteld. Nonuniforme afschuiving kan ovale kernen produceren; `a_i` is dan de oppervlakte-equivalente radius. Materiële segmentlabels moeten bewaard blijven; puntremeshing is niet toegestaan zonder volume-transportmapping. Een `lambda<1` onder de ideal-referentie vereist een aparte *reach*/contact-audit. Curve-tube-dikte, numerieke resolved-core-fysica en stabiliteit blijven open.

## Gebruik

1. Pak deze overlay uit buiten je bestaande A003-map.
2. Stop VortexLab en maak zo nodig zelf een volledige reservekopie.
3. Vanuit de uitgepakte overlay:

```cmd
Apply-P7.cmd --target "C:\workspace\projects\SST-Workbench\05_apps\A003_vortexlab"
```

4. Start VortexLab vanuit de A003-map met `npm start`.
5. Open `http://127.0.0.1:4173/twist-flow/` en selecteer **Gilbert ideal/tight 3:1:1** (vanaf P7 de voorkeursseed). Druk op Reset. Kies eventueel andere `ideal|...` enkelvoudige knoop (bijv. `5:1:2` of `6:1:1`).
6. Bekijk de sectie **P7 / FYSISCHE KNOOPGROOTTE**. `L0`, `λ`, `a_equiv`, lokaal kernbereik, `Rxy` en volumebalans zijn beschikbaar. Exporteer een diagnostisch JSON-rapport met de knop.
7. Selecteer een A006- of KnotPlot-seed om te bevestigen dat Model A **niet actief** wordt. De eerdere achtergrondbundel-P6a blijft een afzonderlijke modus; P7 voegt geen tweerichtings-background-filamentprovider toe.

### Installer

`Apply-P7.cmd` with the included Python standard-library installer is strict: vergelijkt voor iedere gewijzigde doelbron de SHA-256 met exact de bijlage; weigert bestaande maar onverwacht gewijzigde bestanden; detecteert gewijzigde/new file conflicts; maakt een timestamp-backup en rolt terug bij testfout. `--dry-run` voert uitsluitend preflight uit. `--skip-tests` is beschikbaar, maar **niet** aanbevolen. De installer voert `npm run test:twist-flow`, `npm run test:native`, `npm run test:fluid` en `npm run verify` uit. Op Windows moeten Node.js >=20 en Python >=3.9 zijn geïnstalleerd. Optioneel: `py -3 -m pip install SSTcore` voor de afzonderlijke Python API; dit vervangt de native Node.js `sst-core` addon niet.

### Teststatus tijdens patchbouw

- Node-syntax voor nieuwe module, runtime en Twist Flow: PASS.
- `tools/test-model-a-ideal-stretch.mjs`: **10 PASS**, inclusief kunstmatige uniforme/niet-uniforme materiaalrek, translatie, volumebalans, ongeldige segmenten, N- en provenance-gates.
- `npm run test:twist-flow`: PASS.
- `npm run test:native`: PASS.
- `npm run test:fluid`: PASS.
- `npm run verify`: PASS nadat de al in de bijlage **verouderde** KnotPlot-hash is gereconcilieerd naar de exact aanwezige bytes; KnotPlot-data zelf ongewijzigd.
- `npm run check` volledige keten: **NIET PASS** in deze uitvoeromgeving door ontbrekende externe `SSTcore`-module in `test:physics` (dezelfde fout trad al op in de ongewijzigde bron). Native C++/SYCL-providers en volledige browserinteracties zijn niet opnieuw gekwalificeerd.
- Browser end-to-end-test: **NIET GEVALIDEERD**; Chromium-headless bleef tijdens laden hangen; geen valse PASS.

### Bronintegriteit

`reference/source-hashes.json` bevat de P6→P7 keten, P7 hashes en broncatalogus. De aangeleverde oorspronkelijke KnotPlot-hash was `8e7ecfd13cba415a1931d2fcb40558dc783be210116e063a526f855b9fa8bade`; de SHA-256 van de daadwerkelijk meegestuurde KnotPlot-catalogus is `7bd81b1b842a73ff239a54e992e7ca3fff2b7c23f8a596c22df5028c06b543f9`. Alleen het manifest is gereconcilieerd, niet de data. De source hash voor de overige bestanden blijft verifieerbaar met `npm run verify`.

## Bronnen

- H. von Helmholtz (1858), *Über Integrale der hydrodynamischen Gleichungen, welche den Wirbelbewegungen entsprechen*, J. reine angew. Math. 55, 25–55, doi:10.1515/crll.1858.55.25.
- O. Gonzalez & J. H. Maddocks (1999), *Global curvature, thickness, and the ideal shapes of knots*, PNAS 96, 4769–4773, doi:10.1073/pnas.96.9.4769.
- P. G. Saffman (1992), *Vortex Dynamics*, Cambridge University Press, doi:10.1017/CBO9780511624063.
