# Release notes — vortexring-lab v7.5.2

**Basis:** v7.5.1. **Doel:** topologiebehoud afdwingen en Niveau C uit de review implementeren als een discrete driedimensionale exterior-field closure rond de volledige gesloten knooptube.

## Waarom een knoop in v7.5.1 toch kon lijken te breken

De datastructuur verwijderde geen segmenten: ieder filament bleef een cyclische polygonale centerline. Toch waren er drie routes waardoor een breuk of topologieverandering zichtbaar kon worden:

1. Contact werd na een volledige RK4-stap gecontroleerd. Twee segmenten konden elkaar binnen de stap kruisen en aan het einde alweer uit elkaar liggen. Zo'n transient crossing werd niet door een endpoint-test gezien.
2. In LIA-modus was contact slechts een kwalitatieve waarschuwing. De run kon daarom verdergaan terwijl de niet-lokale zelfinteractie ontbrak.
3. Auto-relax muteerde de geometrie buiten de RK4/contact-bisectie om. Een kleine maar ongunstige smoothing- of redistributiestap kon tube-clearance verliezen.

Daarnaast gebruikt de buisrendering een zichtbare minimumradius die groter kan zijn dan `a_sim`. Visueel overlappende buizen zijn daarom niet automatisch een geopende centerline.

## Topology guard

De nieuwe default is `P.topologyGuard=true`.

- De contact-CFL begrenst de tijdstap met de resterende exacte segment-clearance.
- Iedere geaccepteerde stap wordt op exact segmentcontact gecontroleerd.
- Bij tunnelingrisico wordt de RK4-stap op twaalf tussentijden opnieuw opgebouwd.
- De eerste transient contacttijd wordt gebisecteerd.
- De solver landt aan de **veilige** zijde van de contactgrens, niet net eroverheen.
- De guard is ook actief in LIA-modus. LIA mag geen numerieke topologieverandering meer laten passeren.
- Auto-relax is transactioneel: de volledige toestand wordt gesnapshot en teruggezet wanneer de mutatie contact bereikt of een te groot deel van de beschikbare clearance gebruikt.

Er is nog steeds geen reconnectiemodel. Een run stopt vóór een mogelijke doorsnijding; de knoop wordt niet doorgeknipt, herschikt of ontknoopt.

## Niveau C — discrete 3D Neumann-BEM/MFS

De implementatie is een **regularized source-collocation boundary method**, oftewel een kleine method-of-fundamental-solutions/BEM-hybride. Zij benadert de volledige gesloten knooptube in drie dimensies; het is geen reeks losse 2D-doublets.

Voor collocatiepunten \(\mathbf x_i\) met buitenwaartse normaal \(\mathbf n_i\) en fictieve bronnen \(\mathbf s_j\) binnen de uitgesloten tube wordt opgelost:

\[
\mathbf n_i\cdot\left[
\mathbf u_0(\mathbf x_i)
+\sum_j q_j^{(u)}\nabla G(\mathbf x_i,\mathbf s_j)
\right]=0,
\qquad
G=\frac{1}{4\pi|\mathbf x-\mathbf s|}.
\]

Een tweede solve gebruikt hetzelfde Neumannprobleem voor het coarse-grained vorticiteitsveld:

\[
\mathbf n_i\cdot\left[
\boldsymbol\omega_0(\mathbf x_i)
+\sum_j q_j^{(\omega)}\nabla G(\mathbf x_i,\mathbf s_j)
\right]=0.
\]

Daarmee worden twee zaken van elkaar onderscheiden:

- de harmonische velocity-correctie die `u·n=0` op de uitsluitingsbuis benadert;
- het tangentieel geprojecteerde, divergentievrije vorticiteitsveld waarlangs de zichtbare swirl strings worden geïntegreerd.

De compatibiliteitsconstraint \(\sum_jq_j=0\) verwijdert een kunstmatige monopool in het verre veld. De UI toont afzonderlijk het maximale relatieve residu van de velocity- en vorticiteits-Neumannvoorwaarden. Bij een residu groter dan 0.15 wordt de correctie uitgeschakeld.

## Welke tube wordt uitgesloten?

De keuzelijst maakt de status expliciet:

- `a_sim` — default en numeriek oplosbare knooptube;
- `r_kern` — alleen wanneer een geldige vaste kernradius is ingevoerd;
- `R_horn` — uitsluitend als expliciete Research-Track boundary hypothesis.

`R_horn` is niet stilzwijgend tot materiële wand verklaard. Op de meterschaal ligt deze femtometerradius gewoonlijk onder de geometrische BEM-resolutievloer; de solve wordt dan eerlijk geweigerd in plaats van de radius stilzwijgend op te blazen.

## Koppeling aan de filamentdynamica

De exterior BEM-oplossing is niet geldig op de centerline, omdat die binnen de uitgesloten tube ligt. Daarom wordt de bundeladvectie van een filamentpunt bepaald uit het gemiddelde van vier gecorrigeerde buitenveldmonsters op de lokale tube-omtrek. Tracers en stroomlijnen gebruiken de exterior-oplossing rechtstreeks. De BEM-geometrie wordt quasi-statisch iedere acht geaccepteerde stappen vernieuwd.

Dit is een Research-Track closure. Niet inbegrepen:

- een moving-boundary Neumannvoorwaarde met de volledige lokale tube-snelheid;
- pressure/BEM-krachten of added mass;
- een opgeloste microscopische SST-kern;
- reconnectie of GP-doorsteekdynamica;
- bewijs dat `R_horn` zelf een materiële separatrix is.

## Nieuwe zelftests

- **T0l:** topology guard staat standaard aan.
- **T0m:** Niveau-C BEM staat standaard aan met `a_sim` als grens.
- **T0n:** het BEM-bronmodel is geversioneerd.
- **T9j:** uniforme velocity op een gesloten testsfeer wordt tot `u·n≈0` geprojecteerd.
- **T9k:** dezelfde test voor het vorticiteitsveld.
- **T9l:** de compatibiliteitsconstraint geeft `Σq≈0`.
- **T9m:** het transient-contact-risicopredicaat reageert correct.

## Validatie

```text
PASS: statische v7.5.2-integriteitscheck en node --check groen
INFO: 281 statische IDs, allemaal uniek
```

Verplicht lokaal:

```bash
python validate-v7_5_2.py vortexring-lab-v7_5_2.html
npm i puppeteer
node browser-smoke-v7_5_2.mjs vortexring-lab-v7_5_2.html
```

De browser-smoke vereist T0–T9m groen, geen console-/pageerrors, een actieve BEM-readout en een eindige `ε_rev`-meting.
