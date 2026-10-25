# VortexLab modularisatie M1

Bron: `vortexring-lab-v7.6.25b.html`  
Wetenschappelijke versie: **7.6.25b**  
Architectuurmijlpaal: **M1 — parity-safe extraction**

Layout: alles leeft in `05_apps/A003_vortexlab/` (geen aparte `A003-v7.6.25b-m1/` of actieve `vortexring-lab/` map). Archief onder `archive/`; catalog-builders onder `tools/catalog/`; oude parallelle lab-versie in `TO_DELETE/`.

## Wat is gewijzigd

- HTML staat in `apps/web/index.html`.
- CSS staat bytegetrouw in `apps/web/styles/vortexlab.css`.
- De bestaande browserruntime staat bytegetrouw in `apps/web/src/legacy/vortexlab-runtime.js`.
- Three.js en KaTeX worden lokaal uit `apps/web/vendor` geladen.
- Ideal-, Fseries- en KnotPlot-catalogi staan in `apps/web/data`.
- Er is een eerste contractpackage en een proces-geïsoleerde SSTcore-adapterskeleton toegevoegd.

## Wat is nadrukkelijk niet gewijzigd

Geen enkele formule, solverfunctie, gate, catalogusentry of UI-eventhandler is herschreven. M1 verandert alleen bestandsgrenzen en laadpaden.

## Starten

```bash
npm start
```

Open daarna `http://127.0.0.1:4173`.

### Native SSTcore + Twist Flow P4/P5

Actieve patches samen:

- **Twist Flow P4/P5** — dedicated route, motion diagnostics, adaptive CFL (geen vaste 1 µs-vloer).
- **SSTcore native accel** — optionele C++ filamentkernels via companion physics-server.
- Lokale `twist_knot_data.js` / A006-catalogus **niet** overschreven door overlays.

```powershell
npm install
npm run start:native
```

Enable **Native SSTcore** in the lab UI. Zonder server/toggle blijft de JS-solver. Details: [`docs/SSTCORE_NATIVE.md`](docs/SSTCORE_NATIVE.md).

**Note:** WebGL GPU (Arc vs NVIDIA) tekent alleen; de Biot–Savart-solver is CPU tot native C++ aan staat.

## Catalogus (render-only)

3D-overzicht van alle catalogusknopen (ideal / fseries / knotplot / twist), zonder Biot–Savart:

`http://127.0.0.1:4173/catalog.html`

Of via **Knoop uit catalogus** in de lab-header. Per kaart: **Selecteer in lab** →
`index.html?knotSource=…&knotId=…` laadt die knoop. Lazy WebGL-thumbnails; filters en zoekveld bovenaan.

## WebGL / discrete GPU (Arc A770)

De renderer vraagt `powerPreference: 'high-performance'`. **WebGL kan geen GPU kiezen op index of naam** (GPU0 vs GPU1). Op systemen met NVIDIA + Arc kiest die hint vaak de **NVIDIA**, niet de Arc.

Actieve adapter: HUD **WebGL GPU**, console `[VortexLab WebGL]`, of `window.VL_ACTIVE_GPU`.

### Windows 11 — browser vastzetten op Arc A770

1. **Instellingen → Systeem → Beeldscherm → Grafische instellingen**
2. **App toevoegen** → **Desktop-app** → blader naar bv.  
   `C:\Program Files\Google\Chrome\Application\chrome.exe` of  
   `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`
3. **Opties** → kies expliciet **Intel(R) Arc(TM) A770 Graphics**  
   (niet alleen “Hoge prestaties” als Windows dat aan NVIDIA koppelt)
4. Sla op, **sluit alle browservensters/processen** (Taakbeheer → Chrome/Edge beëindigen), start opnieuw
5. Open VortexLab; HUD/console moet `Arc` / `A770` tonen — niet `GeForce` / `GTX` / `NVIDIA`

Optioneel: `chrome://gpu` (of `edge://gpu`) ter controle van de actieve GL-adapter.

## Pariteit controleren

```bash
npm run check
```

De verificatie controleert de SHA-256 van de geëxtraheerde runtime, CSS, catalogi en lokale vendorbestanden.

## Volgende mijlpaal

M2 splitst `src/legacy/vortexlab-runtime.js` per domein met expliciete dependencies, maar alleen nadat de browserbenchmarks van M1 dezelfde resultaten geven als v7.6.25b.

---

## Native XYZ-puntental + tracerbudget — patch p1 (23 oktober 2026)

**Patch-ID:** `native-xyz-resolution-tracer-budget-p1`  
**Runtime:** `7.6.25b-m1-nativeN-p1` — versieerbare aftakking van de M1-bron, niet de bevroren M1-baseline.

### Werking

- Bij **lokale session `.xyz`-import** bepaalt de feitelijke lengte van de coördinatenarray het aantal simulatiepunten van *iedere afzonderlijke gesloten component*. Metadata met `pointCount` wordt hierbij niet vertrouwd boven daadwerkelijke vertices.
- Bij **A006/twist en KnotPlot** worden de oorspronkelijke `.xyz`-vertex-aantallen uit de geconverteerde catalogus (`pointCount` / `pointsPerComponent`) gebruikt. Bij A006 N1024 wordt het native Fourier-rooster rechtstreeks geëvalueerd om extra re-interpolatie te vermijden. De Fourier-conversie blijft een reconstructie, geen certificering van oorspronkelijke topologie.
- Bij **Gilbert ideal, losse `.fseries` en ingebouwde vormen** blijft Laag/Mid/Hoog zoals voorheen actief.
- In **benchmarkmodus met expliciete resolutie-override** blijft de oude doelresolutie gelden: de reeds geregistreerde convergentieladders worden niet veranderd.
- Meerdere linkcomponenten mogen verschillende waarden van `N` hebben. De coördinatenarray van de solver wordt per component met de werkelijke `N` opgebouwd; `fils[i].N` volgt deze lengte.
- Voor automatische oriëntatiedetectie wordt *alleen* een tijdelijke maximaal-N288-proxy gebruikt. Dat verkort de opstartberekening, **niet** het gesimuleerde filament.
- **Passieve flow-tracers** volgen een automatisch budget bij `N_total>288`: `min(gevraagd, max(64, floor(5000×288/N_total)))`. De waarde die de gebruiker heeft ingesteld (`P.tracerCount`) blijft behouden. De daadwerkelijk toegewezen deeltjes worden afzonderlijk weergegeven. Het aantal **vortexpunten** wordt nooit door deze visuele regel verlaagd.
- Bij `N_total>2048` wordt gewaarschuwd voor kwadratische CPU-kosten van volledige Biot–Savart. Er is **geen verborgen downgrade**.

### Voorbeelden van de automatische tracerlimiet

| Totale vortexpunten | Tracers bij gevraagd=5000 |
|---:|---:|
| 288 | 5000 |
| 512 | 2812 |
| 1024 | 1406 |
| 2048 | 703 |
| 4096 | 351 |

### Lokaal testen (Windows, Node.js 20+)

```powershell
npm run check
npm start
```

Open `http://127.0.0.1:4173/`. Selecteer A006 N1024 of laad een eigen `.xyz` en kijk onder **kwaliteit**: `Bronpunten rechtstreeks gebruikt: 1024`. Onder **Visualisatie** staat de visuele tracerlimiet. Vergelijk in lijnmodus en pauzeer vóór dynamische validatie.

### Wetenschappelijke en technische beperkingen

- Deze patch verandert **niet** de Biot–Savart-kernregularisatie, contactdrempels, Euler-sluiting of reconnectie. Hogere resolutie is **geen garantie op stabiliteit**.
- Fourier-catalogi bewaren het door de converter gemelde `N`, niet altijd de originele ruwe `.xyz`-bytes. De lokale `.xyz`-import behoudt wél exact het aantal opgegeven vertices (inclusief eventueel dubbele afsluitpunten, die daarom vóór fysische runs gecontroleerd moeten worden).
- Oorspronkelijke M1-bestanden staan in de `reference/`-provenance. `npm run verify` controleert de nieuwe versiehash én de afzonderlijke baseline-hash.
- Statische en structurele tests slagen; geen claim dat volledige 1024+ Biot–Savart-trajecten al fysisch of temporeel convergeren. Een end-to-end WebGL-browserrun kon in de huidige uitvoeromgeving niet worden gestart (browsernetwerkbeleid).
