# A075-v0.2.9 — Ruban Depositie, Kernresolutie en Geometrietracking

**Status:** DEVELOPMENT_ONLY / PHYSICAL_STABILITY_UNRESOLVED. **Framework:** authentiek, byte-gecontroleerd v1.1.0, ongewijzigd. **Familie:** A075, zelfstandige nieuwe versie naast v0.2.8. **Bron:** Ruban (2018), *Long-lived quantum vortex knots*, figuur 3; de auteursverstoring is niet bekend.

## Waarom deze patch?

De eerdere v0.2.8-diagnostiek van 29 oktober 2026 had zes correct uitgevoerde korte Euler-trajecten, maar (a) de bestaande trefoil met `B0=0.32` kreeg onjuiste Ruban-resolutiemetadata, (b) `config.geometry` vermeldde `0_1` ondanks de daadwerkelijke `initial_condition`, (c) de initiële vorticiteitsdepositie was niet onafhankelijk gekwalificeerd, (d) spectrale verschillen waren geen dynamische topologiemeting.

## Nieuwe functies

1. `experiment/ruban.py`: `resolution_gate(box,grid,sigma,b0)` is nu **per geometrie** correct. De Ruban-referentieparameters delta en xi worden voor de B0=0.32-controle niet als eigen parameters opgevoerd.
2. `experiment/ruban_study.py`: schrijft de werkelijke `config.geometry` en beide geometriespecifieke resolutierapporten. De Euler-operator zelf (`experiment/euler3d.py`) is byte-identiek aan v0.2.8.
3. `experiment/ruban_deposition.py`: onafhankelijke initiele depositie-audit met energie, enstrofie, spectrale randfractie, projectie- en Gaussian-smoothing-L2-verhoudingen, velddoorsneden, afstand-tot-seed, lokale vorticiteitsrichting en een benaderde vorticiteitsrug.
4. Optionele korte evolutie: 96 passieve markerpunten volgen de berekende Euler-snelheid met Heun/trapeziumintegratie, terwijl de vorticiteitsrug **apart uit het actuele veld** wordt bemonsterd. De markers zijn geen automatisch gecertificeerde vorticiteitslijnen. Geen topologiecertificatie.
5. Nieuw standalone `run_all.cmd RUBAN_DEPOSITION`, met geversioneerde uitvoermap en een ZIP + SHA256 naast de versiemap. Geen private keys of revealbestanden in de diagnose.
6. Ongewijzigde oorspronkelijke Framework v1.1.0-runtime. Deze diagnostiek voert **geen** Framework-FREEZE/BASIC/FULL uit en mag de G2/G8/G12-gates niet op PASS zetten.

## Exacte mathematische metingen

De geometrische ratio's zijn `rminor_cells = B0*N/L`, `sigma_cells = sigma*N/L` en `sigma_over_rminor = sigma/B0`, bij R0=1. Voor de twee geometrieen geldt respectievelijk B0=77/500 en B0=8/25.

Voor het in Fourier-coefficienten voorgestelde veld geldt de globale energie:

\[
E=\frac{\rho L^3}{2N^6}\sum_{\mathbf k}|\hat{\mathbf u}_{\mathbf k}|^2,
\qquad
Z=\frac{L^3}{2N^6}\sum_{\mathbf k}|\hat{\boldsymbol\omega}_{\mathbf k}|^2.
\]

De feitelijke code gebruikt de equivalente vorm `0.5*rho*dx**3/N**3 * sum(abs(uh)**2)` met `dx=L/N`. De spectrale randfractie is de verhouding van de enstrofie van modi met `|k_grid| >= 0.7*N/3` tot de totale enstrofie; dit is een **diagnostische shell**, geen universele fysische cutoff.

De lokale veldrug wordt berekend uit een 7x7-stencil in een vlak loodrecht op de lokale **marker**-raaklijn. De gewichten zijn het kwadraat van de positief langs die raaklijn geprojecteerde vorticiteit. De gewogen offset van de rug tot de marker en de lokale richtingsuitlijning worden geregistreerd. Bij `sigma >= rminor` is overlap van naburige takken waarschijnlijk en de interpretatie van een unieke kern ambigu. De vorticiteitsrug is **geen onafhankelijk topologisch invariant**.

De benaderde afstand tot de initiele 2048-puntscurve gebruikt een periodieke dichtstbijzijnde-puntenboom (KD-tree), bij N>96 met gedocumenteerde ruimtelijke subsampling. De resultaten zijn gevoelig voor de initiële filamentdiscretisatie en vormen geen reconstructie van een materiele buis.

**Eenheden:** de studie gebruikt modelschalen R0=1, rho=1, Gamma=2*pi. Getallen kunnen alleen als SI-waarden worden gelezen nadat een consistente meter/seconde/kilogram-schaal is vastgelegd; de waarden zijn niet atomair gekalibreerd.

## Voorgestelde drempels — NIET fysisch gekwalificeerd

- `rminor/dx >= 4` (geometrische vormresolutie).
- `sigma/dx >= 3` (minimale Gaussian-kernresolutie).
- `sigma/rminor <= 0.5` (scheiding tussen kern en kleine torusstraal).
- Relatief verschil in beginenergie tussen naburige roosters < 1% (alleen een **screen**; minimaal drie niveaus voor echte convergentie).

Geen van deze voorwaarden is een bewezen voldoende voorwaarde voor topologiebehoud of lange-duurstabiliteit. Boxvergroting bij vast N wijzigt dx; echte boxgevoeligheid moet bij **vaste dx** worden onderzocht. Rubans delta=0.05 en xi=0.017437... zijn niet gelijk aan de Euler-Gaussbreedte sigma.

## Windows — aanbevolen runvolgorde

Installeer de volledige source-ZIP onder `C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\`. Dit maakt `A075_hydrodynamische_resonante_invanging\A075-v0.2.9` naast de oude versies.

```bat
cd C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A075_hydrodynamische_resonante_invanging\A075-v0.2.9
python -m pytest -q tests
python tools\check_sources.py
python tools\verify_ruban.py

REM Fase 1: regressie, dezelfde parameters als de eerdere 24/32-diagnostiek
run_all.cmd RUBAN_DEPOSITION --deposition-grids 24,32 --deposition-sigmas 0.5 --deposition-boxes 10 --threads 12

REM Fase 2: afzonderlijke sigma-variatie (nog ondergeresolveerd)
run_all.cmd RUBAN_DEPOSITION --deposition-grids 32,48,64 --deposition-sigmas 0.25,0.5 --deposition-boxes 10 --threads 12

REM Fase 3: kleine ontwikkel-box en korte, afzonderlijke veld/marker-tracking
run_all.cmd RUBAN_DEPOSITION --deposition-grids 48 --deposition-sigmas 0.25 --deposition-boxes 6 --deposition-track --track-t-end 0.02 --track-dt 0.005 --threads 12

REM Fase 4 (OPTIONEEL, duurder): eerste kernresolutie-screen; L=4 heeft meer beeldinteracties
run_all.cmd RUBAN_DEPOSITION --deposition-grids 128,160 --deposition-sigmas 0.075 --deposition-boxes 4 --allow-expensive --threads 12
```

**Belangrijk:** fase 4 vereist mogelijk meerdere gigabytes werkgeheugen en veel rekentijd; de runtime blokkeert N>128 zonder `--allow-expensive`. De kleinere periodieke box L=4 is **geen** vrije-ruimte-bewijs. Start deze fase pas na beoordeling van fase 1–3.

## Outputs

- `A075_Hydrodynamische_Resonante_Invanging_v0.2.9-outputs/<run-id>/DEPOSITION_QUALIFICATION.json` — status, voorgestelde drempels, roostervergelijkingen.
- `INITIAL_FIELD_MATRIX.csv` — machineleesbare vergelijking voor beide trefoils.
- `A075-v0.2.9_RUBAN_DEPOSITION_REPORT.pdf` — per-run wetenschappelijk PDF-rapport met vraag, hypothesen, vergelijkingen, resultaten, gates en figuren. Een kopie van het laatst uitgevoerde rapport staat in `../A075-v0.2.9_RUBAN_DEPOSITION_REPORT.pdf`.
- `<L_N_sigma>_<case>.json` — volledige per-case provenance en numerieke observabelen.
- `*_vorticity_xz_y0.npy` — ruwe vorticiteitsdoorsnede (NumPy).
- `*_xz_compare.png` — gedeelde kleurenschaal indien matplotlib geïnstalleerd is.
- `*_markers.npz` en `*_tracking.csv` — optionele trajecten, inclusief apart bemonsterde veldrug.
- `../A075_Hydrodynamische_Resonante_Invanging_v0.2.9-outputs.zip` + `.sha256` — gedeeld diagnose-archief; geen private sleutels.

## Stopcriteria

1. Bronhash niet correct -> STOP.
2. Rooster N niet in 16..256, veelvoud van 8 -> STOP.
3. Grote N of >30 configuratiecombinaties zonder `--allow-expensive` -> STOP.
4. Veld- of markerdata niet-eindig -> exception; geen automatische fysische statuspromotie.
5. `sigma >= rminor` of `rminor/dx < 4` -> **geometrische kwalificatie UNRESOLVED**, ook als de code zonder fouten draait.
6. Geen onafhankelijke finite-core-, box-, tijd-, ruimtelijke en topologische convergentie -> **G12/G8 UNRESOLVED**.

## Herkomst en grenzen

Ruban, V. P. (2018), *Long-lived quantum vortex knots*, JETP Letters 107, 307–311, DOI: 10.1134/S0021364018050120, arXiv:1801.04822. De analytische 2048-puntsseed is een reproduceerbare reconstructie, niet Rubans ongepubliceerde initiële vertices of stoorveld. De bestaande v0.2.8-diagnostiek is alleen input voor deze reparaties, niet nieuw fysisch bewijs.
