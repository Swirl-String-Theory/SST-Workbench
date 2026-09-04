# Cursor-instructies — v7.5.1 → v7.5.2

## Doel

Pas de topology-preserving Niveau-C patch toe op de actuele v7.5.1-build. De patch maakt geen reconnecties; hij verhindert numerieke centerline-doorkruising en voegt een discrete 3D Neumann-BEM/MFS toe voor de achtergrondbundel rond gesloten knooptubes.

## Bestanden na toepassing

- `vortexring-lab-v7_5_2.html`
- `validate-v7_5_2.py`
- `browser-smoke-v7_5_2.mjs`
- `release-notes-v7_5_2.md`

## Toepassen

Vanuit de projectroot:

```bash
git apply --check vortexring-lab-v7_5_1-to-v7_5_2.diff
git apply vortexring-lab-v7_5_1-to-v7_5_2.diff
```

Deze patch hernoemt de hoofd-HTML van v7.5.1 naar v7.5.2 en voegt de drie begeleidende bestanden toe.

## Statische validatie

```bash
python validate-v7_5_2.py vortexring-lab-v7_5_2.html
```

Verwacht:

```text
PASS: statische v7.5.2-integriteitscheck en node --check groen
INFO: 281 statische IDs, allemaal uniek
```

## Browser-smoke

```bash
npm i puppeteer
node browser-smoke-v7_5_2.mjs vortexring-lab-v7_5_2.html
```

De smoke moet minimaal bevestigen:

- ≥10 renderframes;
- geen console- of pageerrors;
- zelftest v7.5.2 volledig groen;
- T0l, T0m, T0n en T9j–T9m aanwezig;
- `Topology guard` standaard aan;
- `Niveau C` standaard aan;
- actieve BEM-readout zonder `lineaire solve mislukt` of `residu te groot`;
- `ε_rev` eindig bij `α=0`.

## Handmatige acceptatie

1. Open de standaard SST-trefoil.
2. Zet de SST-vortexbundel en de bundelveldkoppeling aan.
3. Controleer dat de representatieve bundellijnen vóór de knooptube uiteenlopen, tangentieel langs de tube lopen en erachter weer aansluiten.
4. Controleer in de BEM-readout dat zowel `residu u_n` als `residu ω_n` eindig zijn. Richtwaarde: ruim onder `1e-1`; de code schakelt de correctie boven `0.15` uit.
5. Verhoog drift of simulatiesnelheid totdat zelfcontact wordt benaderd. De run moet stoppen met een topology-guardmelding; de centerline mag niet door zichzelf heen verschijnen.
6. Herhaal met LIA. De guard moet ook daar hard stoppen, niet alleen waarschuwen.
7. Zet Auto-relax aan nabij de contactgrens. Een onveilige regularisatiestap moet worden teruggedraaid en Auto-relax moet zichzelf uitschakelen.
8. Schakel de centerline-overlay in om visuele buisoverlap te onderscheiden van echte centerline-doorkruising.

## Fysische interpretatie

De default BEM-grens is `a_sim`. Dit is de numerieke knooptube, niet automatisch `r_kern` of `R_horn`.

- `r_kern` is alleen selecteerbaar wanneer die Research-Track invoer is opgegeven.
- `R_horn` blijft een expliciete hypothese. Omdat deze femtometerschaal niet op de meterschaalmesh wordt opgelost, mag de BEM-solve die keuze weigeren wegens de geometrische resolutievloer.
- De solve is quasi-statisch en gebruikt source-collocation/MFS; noem haar niet een exacte continuum-BEM of een opgeloste SST-kern.

## Niet accepteren wanneer

- `node --check` rood is;
- dubbele statische IDs bestaan;
- de topology guard in LIA slechts waarschuwt en verder integreert;
- `bisectFirstHit()` bij actieve guard aan de contactzijde (`hi`) landt;
- de BEM-correctie op de centerline zelf wordt geëvalueerd in plaats van via tube-oppervlakmonsters;
- bent bundle lines onafhankelijk van de knoop worden geroteerd;
- `R_horn` stilzwijgend naar een grotere numerieke radius wordt geklemd;
- de browserzelftest of BEM-readout rood is.
