# B007 — Atlas Integration & Geometry Cross-Validation

Datum: 30 oktober 2026. Status: **gepland, bronselectie gepind; geen uitvoeringsvrijgave**.
Basis: bestaande B007 v0.2.3, inclusief de aanwezige HF1-bronpariteitscontrole.
Voorgestelde nieuwe implementatieversie: **v0.2.4**, uitsluitend nadat de catalogusidentiteit is opgelost en de doelmap vrij blijkt. v0.2.3 bestaat al en blijft ongewijzigd.

## Besluit en scope

B007 wordt de eerste geplande nieuwe atlasintegratietranche. Nu zijn uitsluitend brononderzoek, integriteitscontrole, gerichte reader-loads en dit plan uitgevoerd. De volgende softwarestap krijgt een kleine expliciete referentieset; numerieke kwalificatie en verdere fysica blijven afzonderlijke tranches.

De bestaande Scheduled-taak, A054-wachtrij, algemene campagnevrijgave en A011/A054/A065-contracten zijn door deze B007-planning niet veranderd. Een planning is geen toestemming voor dynamica. Er is geen nieuwe B007-versiemap gemaakt.

## Actueel gecontroleerde uitgangssituatie

- De zelfstandige E010 v0.4.0-verifier slaagde: **52.596 payloadbestanden**, **11.757 logische records**, **14 representatieve geometrieën**. Dit is integriteit/import, geen nieuwe topologische of dynamische kwalificatie.
- Daarna zijn de vijf hieronder gekozen records afzonderlijk via de bestaande `CombinedSeedAtlas` geladen. Zowel bronbytes als geordende geometriehashes slagen; de nominale/verstoorde ouderrelatie en de exacte kopie zijn gecontroleerd.
- **81 invoerbestanden** zijn gehasht: atlaspublicatie, index, reader/parsercode, geselecteerde bronnen, historische bronmetadata, relevante B007-code/configuratie/tests/protocol en beide catalogusindices. Zie `INPUT_HASHES.json`.
- De atlas bevat **303 groepen met exact dezelfde geordende geometriehash**. Dat is geen volledige detectie van gelijkheid na rotatie, translatie, herparametrisatie of isotopie.
- Voor het label `3_1` zijn er 673 records, waarvan 189 historisch. Alle 189 dragen de bewaarde geaggregeerde topologiestatus `FAIL`. Dit betekent niet dat deze inspectie hun knooptype heeft weerlegd. Individuele metriekgates en onopgeloste convergentie blijven apart zichtbaar.
- B007 v0.2.3 heeft al een op T(2,3)-Ruban toegespitste atlasroute met N2048/N4096-consumerdatasets en gescheiden tweelevel ruimte-/tijdvergelijkingen. Een gezamenlijke Ruban/KnotPlot/Fremlin-import ontbreekt. De historische claim van 57 geslaagde tests is gelezen, niet opnieuw uitgevoerd.
- Registratie is nog niet sluitend: `catalog_index.json` bevat B007 niet; `family_hierarchy.json` noemt B007 uitsluitend als volgende beschikbare B-identifier. De lokale `FAMILY.yaml` meldt `UNASSIGNED_REQUIRES_CURRENT_INDEX`.
- Een historische carrier verwijst naar `logfiles/effectiveness.dat`, met regels zoals `1 0 0`, terwijl de bron als XYZ is geïndexeerd. Die byte-integriteit bewijst geen geometrische betekenis. Deze bron blijft bewaard maar wordt expliciet uitgesloten van de B007-selectie. Geen automatische selectie van alle records met hetzelfde topologielabel.

## Kleine, vooraf vastgelegde referentieset

1. **Ruban nominal:** `RUBAN_v036_T_2_3_B2000_N1024_nominal`, T(2,3), B0=0,20, 1.024 punten. Eén analytische embedding; selectie voor importdekking, niet op een dynamisch resultaat geoptimaliseerd.
2. **KnotPlot:** `CAR_31cb4dd7832f3462`, oorspronkelijke opgeslagen polygoon met **300 punten**. Bestaande historische `FAIL`/`UNRESOLVED`-gegevens blijven behouden.
3. **Fremlin:** `CAR_212795fc5320f974`, oorspronkelijke Fouriercoëfficiënten; de bestaande reader evalueert deze op **4.096 punten**. De coëfficiënten zijn de bron; 4.096 is de evaluatieresolutie.
4. **Verstoringscontrole:** `RUBAN_v036_T_2_3_B2000_N1024_perturbed`. Behoud parent-ID, perturbatiebeleid en dezelfde analytische brongroep.
5. **Duplicaatcontrole:** `CAR_a7c802004bcfe26f`, exact dezelfde geometrie als de gekozen KnotPlot-bron. Het afzonderlijke bronrecord blijft bestaan en telt niet als extra embedding of onafhankelijke bron.

Alle vijf krijgen voor deze voorgestelde consument **DIAGNOSTIC_CANDIDATE_ONLY**. `research_only=false` bij historische records betekent niet automatisch productie-admission. De oorspronkelijke atlasstatussen worden nooit overschreven. Een overeenkomend `3_1`-label bewijst op zichzelf geen gelijke chiraliteit, oriëntatie of gekwalificeerde isotopie.

## Broncontract

`SOURCE_SELECTION.json` bewaart de exacte records, oorspronkelijke kwalificaties, bronpaden, variantrelaties en hashes. `DATASET_ADMISSION_CONTRACT.proposed.json` legt het voorgestelde consumentencontract vast. De voorstelbestanden zijn met SHA-256 verzegeld, maar zijn nog geen actief productiecontract of campagnebudget.

Vereiste invoervelden zijn: atlasversie en indexhash, record-ID, bronpad en raw-hash, parser-/generator-/configuratiehashes, geordende geometriehash, componentvolgorde, bronrepresentatie, bronpuntaantal versus evaluatiepuntaantal, oorspronkelijke eenheden, topology-label en kwalificatiebewijs, chiraliteit/oriëntatie, embedding-ID, lineage/provider-brongroep, duplicate-group, variant en parent-ID, historische gates en afzonderlijke consumer-admission.

Lokaal aanwezige bronnen zijn **user-authorized**. Dat is geen claim van onafhankelijke uitgeversauthenticatie. Een hashverschil, onveilig pad, ontbrekende component of onjuiste bronbetekenis blokkeert de betreffende invoer. Onvoldoende wetenschappelijke kwalificatie houdt een integere bron diagnostisch.

## Twee gescheiden vergelijkingsassen, plus tijd

### Ruimtelijke resolutie binnen dezelfde embedding

Voorgestelde niveaus: N=1.024, 2.048 en 4.096. Houd bronidentiteit, geometrieparameters, componenten, perturbatie, schaal, circulatie, kerninstelling en eindtijd gelijk. Alleen de ruimtelijke discretisatie verandert.

- Ruban: evalueer dezelfde gepinde analytische formule opnieuw op elk N. Controleer eerst aansluiting op de oorspronkelijke N1024-bytes/geometrie met de bestaande strikte bronpariteitsregels. Een hoger N is geen nieuwe onafhankelijke bron.
- Fremlin: gebruik `sample_fremlin_fseries` op exact dezelfde gepinde coëfficiënten, met bevroren fase en conventies. Een grotere N voegt geen nieuwe Fouriermodi toe.
- KnotPlot: de gekozen bron heeft 300 punten. Interpolaties naar 1.024/2.048/4.096 mogen alleen als **POLYGON_REPRESENTATION_REFINEMENT** worden gerapporteerd. Ze kunnen gevoeligheid van de berekening voor de bemonstering van die polygoon onderzoeken, maar sluiten geen fout ten opzichte van een onbekende gladde broncurve. Voor zo'n claim is een apart gekwalificeerde hogere-resolutiebron van aantoonbaar dezelfde embedding nodig. Een nieuwe relaxatie is mogelijk een andere embedding.

Sla `source_N`, `evaluation_N`, `dynamic_N`, sampler, referentiegeometrie en resamplingbeleid apart op. Laat de generieke `run_pair`-route niet ongemerkt een tweede interpolatie toepassen: de adapter moet zijn uiteindelijke invoerhash en puntentelling vastleggen.

### Embeddinggevoeligheid binnen hetzelfde topologielabel

Vergelijk de drie oorspronkelijke embeddings bij vergelijkbare, voldoende gekwalificeerde numerieke instellingen. Bevries één schaalbeleid, circulatie, kernverhouding, eindtijd, temporele discretisatie en metriekdefinities. Bewaar native geometrieën apart van afgeleide genormaliseerde invoer.

Voorgesteld voor het latere vergelijkingsprotocol: één gedeelde totale-lengteconventie, met één vaste schaalfactor per embedding en over alle N-niveaus; geen nieuwe schaalfit per N. Dit wordt vóór uitvoering expliciet verbonden aan B007's dimensieloze R0/Gamma/kern-/tijdconventies. Zonder die verbinding is dynamische vergelijking geblokkeerd. Geen automatische SI-conversie.

Puntindex-op-puntindex Kabsch-afstanden veronderstellen overeenkomstige materiaalpunten. Gebruik die niet zonder correspondentie als bewijs van verschil tussen onafhankelijke embeddings. Leg chirality/orientation en eventuele fasekeuze vast; spiegel niet stilzwijgend om overeenstemming te verbeteren. Analyseer echte embeddingverschillen naast de afzonderlijk gemeten numerieke onzekerheid, zonder nieuwe wetenschappelijke drempels uit de uitkomsten af te leiden.

### Temporele convergentie

Een latere, afzonderlijk vrijgegeven numerieke tranche gebruikt bij vaste geometrie en N bijvoorbeeld dt, dt/2 en dt/4, steeds tot dezelfde eindtijd. Ruimtelijke en temporele effecten krijgen afzonderlijke ledgers; wijzig N en dt niet alleen gelijktijdig. Bestaande tweelevel-consistentie blijft diagnostisch en wordt geen drielevel-convergentieclaim.

De huidige toleranties en HF1-roundoffgrenzen blijven behouden. Nieuwe acceptatiecriteria, rekentijdlimiet en aantallen stappen moeten vóór uitvoering expliciet worden vastgelegd; deze planning geeft geen numeriek campagnebudget vrij.

## Patchvolgorde voor de eerstvolgende softwarestap

1. **P01 — Catalogus en versie.** Controleer de actuele centrale identiteit en bezetting; reconcileer de B007-familie via bestaande indexbouwers. Bewaar bestaande mappen en resultaten. Maak daarna alleen een vrije opvolgversie, voorgesteld v0.2.4. Bewaak dat geen andere familie of standaardselectie verandert.
2. **P02 — Kleine adapter.** Voeg een B007-consumentenadapter met expliciete record-allowlist toe. Hergebruik `CombinedSeedAtlas`, het bestaande `Carrier`-model en de originele parsers. Hash de reader en zijn afhankelijkheden. Geen parallelle atlasreader of wijziging van E010 v0.4.0.
3. **P03 — Sampling en provenance.** Maak de drie bronrepresentaties expliciet; registreer immutable afgeleide geometrieën, N, parent-ID, schaal en hash. Houd integriteit, bronsemantiek, geometrie-admission en wetenschappelijke status gescheiden. Respecteer alle componentgrenzen.
4. **P04 — Onafhankelijke registraties.** Scheid spatial-resolution, temporal-resolution en embedding-comparison. Leg bronrecordaantal, unieke geordende geometrie, embedding-lineage en providergroep afzonderlijk vast. Tel de KnotPlot-kopie niet dubbel; Ruban nominal/perturbed blijven dezelfde analytische brongroep.
5. **P05 — Veilige verificatie-ingang en rapporten.** Voeg een expliciete import-/verificatiemodus toe zonder evaluatoren; geef die het eigen create-only run-ID en ledger. Breid bestaande B007-rapportage/verpakking uit en houd het technische intakerapport gescheiden van wetenschappelijke conclusies. Pas het centrale outputcontract toe waar relevant; label B007 niet automatisch als Framework v1.0.10-gekwalificeerd.
6. **P06 — Acceptatie.** Test corruptie, ontbrekende bron/component, conflicterende IDs, onveilige paden, reader-pindrift, logfile-exclusie, exact duplicaat, bron-/evaluatieresolutie, parent/providerbehoud, componentvolgorde, niet-toegelaten productiegebruik en herhaalde create-only runs. Verifieer JSON-ledger/PDF-consistentie en ZIP/SHA-256; render het PDF. Geen Heun-, native- of Euler-run in de importsmoke.

De bestaande `run_all.cmd` zonder argumenten start een dynamische pilot na tests. Die ingang is voor deze plan-/importfase niet uitgevoerd. Een toekomstige veilige verificatiemodus moet expliciet worden toegevoegd en getest; het plan presenteert geen nog niet bestaande opdracht als werkend.

## Doorgang naar de volgende tranches

1. **Nu — atlas en broncontract:** integriteit/import geslaagd, selectie gepind als voorstel. B007-registratie en consumer-adapter nog open; wetenschappelijke admission blijft diagnostisch.
2. **Eerstvolgende softwarepatch — adapter:** alleen doorgang na juiste catalogusidentiteit, vrije opvolgversie, reproduceerbare import en geslaagde negatieve tests. Geen dynamica nodig voor deze softwaregate.
3. **Numerieke kwalificatie — meerdere embeddings:** pas na een vooraf vastgelegd en afzonderlijk vrijgegeven budget, bevroren schaal-/kern-/tijdprotocol, passende bronresolutie en gescheiden ruimtelijke/temporaliteitscriteria. Onvoldoende gekwalificeerde bronnen leveren uitsluitend diagnostiek.
4. **Geometrie/finite-core — A006 en VortexLab:** eigen tranche met bereik, kernscheiding, schaling, componenten, topologie en conserveringsvereisten. Geen automatische toelating vanuit een import-PASS.
5. **Gekoppelde dynamica — volledige Euler-tests:** eigen tranche met geldige beginvelden, voldoende spectrale resolutie, passende domein-/randvoorwaarden en onafhankelijke numerieke controle.
6. **Brede uitrol:** alleen per falsifier expliciet dataset-admission-contract en uitvoeringsvrijgave. Geen uitbreiding van Scheduled door dit plan.

## Acceptatie van dit plan

Bronintegriteit en vijf reader-loads zijn gecontroleerd; het voorstel bevat exacte bronkeuzes en controleerbare patches. Softwaremigratie, numerieke uitvoering en wetenschappelijke kwalificatie zijn **niet uitgevoerd**. Volgende concrete actie: implementeer na opdracht P01-P06 als begrensde import-/rapportagepatch in een nieuwe versie; reserveer dynamica voor de afzonderlijke numerieke tranche.
