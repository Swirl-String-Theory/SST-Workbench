# Gate2 v0.2.0 — wetenschappelijk protocol en beslisregels

## Vier gates, afzonderlijke scopes

G1: Reproduceerbare analytische 3D-torusknoop/link-constructie, sluitende discrete polygonen, eerste elementaire afstandscheck. Geen reach-certificering.

G2: Finite-time regularized filament heuristic. De knooplijnen ondervinden binnen het model hun eigen en onderlinge Biot-Savart-inductie. Stappen met Heun zijn geen volumebehoudende 3D-Euler-transporten. Registreer ook `segment_over_xi` en `dt_over_xi2`. De ingestelde ruimtelijke preflight is slechts een screeningheuristiek en geen convergentiecertificaat. Het initiële rigide residu en de eindvormdrift worden afzonderlijk opgeslagen; het rangschikkingsgewicht is uitsluitend een expliciete **heuristiek**.

G3: Selectie per embedding op de beste `(B0,Lambda)` in G2. Behoud de volgorde van scores bij onafhankelijke N-verfijning; rapporteer relatieve en absolute verandering. Gebruik E010 v0.3.6-analytische bronformule voor *dezelfde* geselecteerde kandidaat met hogere N. Een gegenereerde knooplijn wordt niet automatisch een finite-core-vorticiteitsveld.

G4: Constructie van periodieke Gaussian-mollified, spectraal divergence-free 3D-vorticiteitsvelden, met één gezamenlijk Biot-Savart-snelheidsveld voor alle componenten. `rhs = curl(u_total cross omega_alpha)` per materiaalcomponent. Als periodieke-translatiekandidaat is het stationair-residu `R_alpha=rhs_alpha+U_z d_z omega_alpha`; slechts één U wordt op het trainingsrooster bepaald en op het holdoutrooster bevroren. Controleer **max over alle componenten** en rapporteer filterwijziging per component. Bij ruimtelijke filtering >10%: numerieke preflight FAIL. Bij te kleine intercomponentafstand/retourgeometrie: geometrische BLOCK. Nooit G2 PASS uit deze coarsed-grid resultaten.

## Wat is nodig voor een toekomstige G2 PASS?

(i) Een werkelijke full-field oplossingszoeker over een voldoende rijke familie van topologiebehoudende materiële diffeomorfismen van de totale vorticiteit (alle levende componenten), met fixering van symmetrievrijheden.

(ii) Bevroren, niet-triviale kandidaat en onafhankelijk convergerende per-component Euler-vorticiteitsresiduen op voldoende fijne 3D-domeinen, en dezelfde voorspelde vormvaste beweging.

(iii) Onafhankelijke Biot-Savart/backend, domein- en randvoorwaardengevoeligheid, ruimtelijke en temporele convergentie bij dezelfde fysieke eindtijd.

(iv) Circulatie/helix- en materiële topologiecontroles, tube-reach, strikte scheiding van de retourlussen en niet-smooth field mixing.

Een 'stabiel' of quasi-stabiel filament in een gereduceerd model voldoet niet aan dit bewijs. Een negatieve G4-run met onderopgeloste kern falsifieert het bestaan van een optimaal gekoppeld evenwicht evenmin.

## Modellimieten

De standaard Euler-pilot gebruikt `Gamma_total_knot = 1` (links: gelijk over componenten verdeeld), `R0=1`, een periodiek kubusdomein en per achtergrondslinger `Gamma_B=0.05`. Dit is een dimensieloze modelkeuze, geen SST-parameterfit. De Lambda-regel `xi=exp(-Lambda)` geldt alleen voor de **gereduceerde filamentberekening**. De G4-Gaussian-parameter `sigma` is onafhankelijk; de software doet niet alsof beide identiek zijn.
