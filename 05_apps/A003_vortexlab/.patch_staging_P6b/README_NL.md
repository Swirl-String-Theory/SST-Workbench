# A003 VortexLab — P6b Discreet ↔ Continuüm (experimentele patch v0.1.0)

**Doel:** een expliciete keuze tussen een voorgeschreven macroscopisch rotatieveld en een **discreet rooster van wederzijds geïnduceerde, beweeglijke wervelcentrelijnen** op de bestaande Twist Flow-pagina. De bestaande originele A003-versie wordt **niet automatisch gewijzigd**.

**Bevroren input**: `05_apps/A003_vortexlab/` uit de verbonden Google Drive op 26 oktober 2026, inclusief Twist Flow P6a; `src/legacy/vortexlab-runtime.js` gebaseerd op 7.6.25b-M1-P5. Vier exacte SHA-256-ingangshashes in `manifest.json`. Alle wijzigingen beperken zich tot de vier daarin genoemde bestanden.

## Wat werkt

- **Uit:** geïsoleerde knoop, standaardgedrag en oorspronkelijke solverroute.
- **Continuüm:** de bestaande P6a-modus gebruikt de opgelegde Rankine-achtige rotatie met `cSSTBundle/cBundleFlow` en optioneel statische randelementencorrectie (BEM, *Boundary Element Method*). Dit zijn géén losse achtergrondwervelkernen.
- **Discreet:** nieuwe `window.__vlDiscreteBundleAPI`; een NxN vierkant rooster van 1, 9 of 25 eindige open filamenten (9, 17 of 25 punten per filament) langs z. Ze worden getoond als turquoise lijnen. De punten in het interieur worden dynamisch bewogen door (a) alle achtergrondfilamenten en (b) de gesloten knoop; omgekeerd beïnvloedt het actuele achtergrondrooster de knoop in **dezelfde gezamenlijke viertraps-RK4-stap**. Eindpunten zijn vastgehouden. Geen statisch getekend pseudo-rooster.
- **Tracers en stroomlijnen** krijgen in discrete modus dezelfde aanvullende achtergrond-Biot–Savart-snelheid.
- `Γ_b = 2 Ω d²`, `n=1/d²`, `⟨ω_z⟩=nΓ_b=2Ω`. De stroomfuncties gebruiken SI-eenheden (meter, seconde, m²/s).
- Modewisseling pauzeert en reset de toestand. Continuüm-BEM en discrete Biot–Savart staan nooit tegelijkertijd aan. Het koppelingscentrum wordt niet vastgepind, periodiek z-wrappen voor de hoofdcomponenten wordt uitgeschakeld en de knoopcontactguard blijft actief.
- Contact tussen knoop en achtergrond en tussen verschillende achtergrondfilamenten wordt met de segment-segment-afstand bewaakt, met de bestaande numerieke contactdrempel. Een eventueel gebisecteerde contactstap zet **zowel knoop als achtergrond** terug en integreert opnieuw. Onmogelijke of niet-eindige toestanden worden teruggedraaid.
- De actieve toestand en de maximale laterale achtergrondverplaatsing zijn afleesbaar via de status en `window.__vlDiscreteBundleAPI.getSnapshot()`.

## Installatie (alleen op exact overeenkomende basis)

1. Pak deze ZIP uit naar een tijdelijke map **buiten** `A003_vortexlab`.
2. Open PowerShell in de uitgepakte patchmap.
3. Controleer de inhoud en de oorspronkelijke basisbestanden:

   ```powershell
   python install_patch.py --root "C:\workspace\projects\SST-Workbench\05_apps\A003_vortexlab"
   ```

4. Alleen als voor **alle vier** bestanden `BASELINE` wordt gemeld:

   ```powershell
   python install_patch.py --root "C:\workspace\projects\SST-Workbench\05_apps\A003_vortexlab" --apply
   ```

5. De installer bewaart de exacte oude bestanden met SHA-256-verificatie onder `.A003_P6b_backups/<UTC-timestamp>/`. **Geen force-modus**: bij `MODIFIED_OR_UNKNOWN` of `ALREADY_PATCHED` naast `BASELINE` wordt installatie geweigerd. Herstel lokaal via die back-up indien nodig.
6. In de A003-root: controleer de syntax en de bestaande niet-pariteitstests en start daarna de app:

   ```powershell
   node --check apps/web/src/legacy/vortexlab-runtime.js
   node --check apps/web/twist-flow/twist-flow.js
   npm run test:twist-flow
   npm run test:fluid
   npm start
   ```

   Open `http://127.0.0.1:4173/twist-flow/`. Schakel voor discrete modus eerst **SST-kandidaat** in bij de mediumselectie (dus geen vrije demo-Γ), kies daarna ‘Discreet rooster’. De bestaande `npm run check` bevat **een bevroren bytehashpariteitscontrole** (`tools/verify-parity.mjs`) van de oude runtime. Die zal de bewust gewijzigde runtime als verschil afkeuren. Behoud die oorspronkelijke baseline en toets de nieuwe vier SHA-256-waarden apart met `manifest.json` en `python install_patch.py --root <pad>`; dit is geen wetenschappelijke pariteitscertificering.
7. Selecteer bij voorkeur een lage N voor eerste tests; standaard selecteert Twist Flow mogelijk een A006 N1024-preview en die is duur bij volledige Biot–Savart. Zet bewegingsdemo en native preview uit voor een wetenschappelijke vergelijking.

## Omschakelformule

Voor een vierkant rooster, met gelijkgerichte circulaties:

\[
\Omega=\frac{\Gamma_b}{2d^2},\qquad
\Gamma_b=2\Omega d^2,\qquad
\bar\omega_z=2\Omega.
\]

Bij bijvoorbeeld `Ω=1 s⁻¹`, `d=0.06 m` is `Γ_b=0.0072 m²/s` per achtergrondkern. Dit is de **ruimtelijke gemiddelde** dichtheidsrelatie voor een hypothetisch uitgebreid rooster, **niet** een exacte profielgelijkheid voor een begrensde 3×3- of 5×5-verdeling. Die eindige pakketten hebben sterke rand- en eind-effecten.

## Wetenschappelijke grenzen (essentieel)

1. **Research Track, niet Euler-gecertificeerd.** De filamenten zijn eindige **open**, met vastgehouden eindpunten, en hebben geen fysisch afgeleide eindstructuur of periodieke z-Greenfunctie. Een open wervellijn zonder geschikte grens/retour kan niet als volledige globale wervelconfiguratie van een gladde incompressibele Euler-vloeistof worden opgevat. Dit is een *tweewegs tijdsevoluerend filament-surrogaat*, geen bewijs van stabiele Euler-kernen.
2. De segmenten gebruiken **midpoint-geregulariseerde** Biot–Savart met `a_sim²` in de noemer; de bestaande knoopkern behoudt zijn eigen lokale-inductieformule. `a_sim` is numerieke softening, geen bewezen fysische SST-kernradius.
3. Druk-Poisson-sluiting, stroomlijn-wandvoorwaarden, kernvolume-evolutie en exacte heliciteitsbehoud/grootheid zijn niet geïmplementeerd. Vanwege de vaste eindpunten mag een totale energie- en impulssom niet als behoudswet van een vrij systeem worden geïnterpreteerd.
4. De gewone axiale uniforme snelheid uit de bestaande solver is **niet** als identieke Galileïsche translatie van de vastgehouden achtergrondeindpunten behandeld. Voor modelvergelijkingen moet de opgelegde axiale snelheid nul zijn of afzonderlijk als randvoorwaarde worden afgeleid.
5. De discrete kernoriëntaties blijven open lijnen, niet gefingeerde gesloten filamenten; eindpunten en geometrie zijn gevoelig voor de z-lengte.
6. De bestaande contactguard is uitgebreid voor discrete lijnen, maar een **volledige** incident-/reconnectieproof en ruimtelijke/tijdelijke convergentie ontbreken.
7. Gebruik deze patch niet voor bewijs over fysieke stabiliteit van een trefoil zonder blind knoop-/roostercontrole, nulbundelpariteit, timestep-ladder, roosterresolutieladder, kernradius-scan, perturbaties en eerlijke vergelijking met de continue limiet.

## Uitgevoerde controles

| Gate | Resultaat | Betekenis |
|---|---|---|
| B0: exacte Drive-baselines | PASS | Vier bronhashes vastgelegd |
| B1: JavaScript-parsing | PASS | Runtime en Twist Flow UI `node --check` |
| B2: gesloten omzetformule | PASS | Γ↔Ω bij vaste d, SI-consistente uitkomst |
| B3: tweewegs-inductie | PASS (geïsoleerd) | Knoop en achtergrond bewegen beide onder dezelfde RK4-stap |
| B4: rollback en eindpunten | PASS (geïsoleerd) | Exact herstel van achtergrond en vaste uiteinden |
| B5: nulsterkte | PASS (geïsoleerd) | Γ_b=0 geeft geen extra knoop-/tracersnelheid |
| B6: volledige browser-opstart | **NIET UITGEVOERD** | Testbrowser blokkeert lokale HTTP-server (ERR_BLOCKED_BY_ADMINISTRATOR) |
| B7: knoop-/roostercontact integraal | **LOKAAL NOG TE TESTEN** | Geometrische integratie in runtime is geschreven, maar browserrun ontbreekt |
| B8: Euler- en finite-core-certificering | **OPEN** | Druk, randvoorwaarden en resolutie/convergentie ontbreken |

De pakket-tests worden uitgevoerd via `node tests/test_discrete.js` en `python tests/test_package_contract.py`. Beide zijn **gedeeltelijke** verificaties, geen bewijs van fysische juistheid. Bestaande `npm run test:twist-flow` en `npm run test:fluid` zijn **niet** in de volledige lokaal draaiende A003-repository uitgevoerd; rapporteer eventueel falen of regressies afzonderlijk.

### Pariteitsbeleid

Deze patch maakt bewust nieuwe solverfysica en kan **niet** een M1-pariteitstest met de oorspronkelijke runtimehash doorstaan. Daarom blijven `reference/source-hashes.json` en `tools/verify-parity.mjs` ongewijzigd. `manifest.json` legt exact de vier oude en vier nieuwe SHA-256-hashes vast en de bewaakte installer controleert deze inclusief back-up en herhaalbaarheid. Voor toekomstige productiecertificering is een apart, expliciet P6b-provenanceprofiel in de oorspronkelijke projecttestinfrastructuur nodig.

## Bronnen

- H. Helmholtz (1858), Über Integrale der hydrodynamischen Gleichungen, welche den Wirbelbewegungen entsprechen, *Journal für die reine und angewandte Mathematik* **55**, 25–55. https://doi.org/10.1515/crll.1858.55.25
- G. K. Batchelor (1967), *An Introduction to Fluid Dynamics*, Cambridge University Press. https://doi.org/10.1017/CBO9780511800955
- P. G. Saffman (1992), *Vortex Dynamics*, Cambridge University Press. https://doi.org/10.1017/CBO9780511624063
