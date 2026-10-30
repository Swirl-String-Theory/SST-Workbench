# Gate2 Coupled Trefoil–Background v0.1.0 — DEVELOPMENT

**Resultaat:** reproduceerbare gekoppelde 3D Euler-proef voor twee verschillende
Ruban-torus-trefoil-embeddings, maar **GEEN gevonden gezamenlijk relatief
evenwicht** (`G2_COUPLED_UNRESOLVED_NO_JOINT_EULER_EQUILIBRIUM`).

De oorspronkelijke XYZ-coördinaten uit `Ruben_T_2_3_T_3_2.zip` zijn ongewijzigd
meegenomen in `source_data/`:

- `T_2_3_B1600_N512.xyz` (512 vertices, torusminor B=0.16)
- `T_3_2_B1600_N512.xyz` (512 vertices, torusminor B=0.16)

De Python-code maakt gladde Gaussian-gespreide, analytisch solenoïdale
vorticiteitsvelden van de gesloten polygonen. Een tweede volledig levende,
gesloten 'racetrack'-kern heeft een aanvankelijk recht deel langs de `z`-as,
met een echte retourtak verderop. Het *totale* snelheidveld voert beide
vorticiteitscomponenten dynamisch mee. Er worden geen SST-constanten
(Swirl-String Theory) ingeladen.

## Windows

```
py -m pip install -r requirements.txt
run_all.cmd
run_all_extended.cmd
```

`run_all.cmd` draait `pytest` en twee seeds op `32^3` met drie kleine
Runge–Kutta-tijdstappen. `run_all_extended.cmd` draait `48^3` en `64^3`,
eveneens drie tijdstappen. Voor de uitgebreide tests zijn voldoende
werkgeheugen en vrije ruimte nodig. Iedere simulatie is een apart proces.

Het evaluatieoverzicht kan opnieuw worden gemaakt met

```
py src\assess.py
```

Op Linux/macOS: `bash run_all.sh`.

## Experimentele configuratie

- Domein: periodieke kubus `[-3,3)^3` (afwijkend van vrije ruimte)
- Trefoilcirculatie: `Γ_K=1`, achtergrondcirculatie: `Γ_B=0.05`
- Gladstrijklengte: `σ=0.12` (niet compacte support)
- Hoofdtak achtergrond: `(x,y)=(0,0)`, `-1.3 < z < 1.3`
- Retourtak achtergrond: `(x,y)=(2.0,0)`, met afgeronde boven-/onderzijde
- Geen vloeiende gehele-rotsymmetrie op de kubische periodieke ruimte;
  alleen `z`-translatie wordt gefit, geen `Ω`-rotatie
- `32^3`, `48^3`, `64^3`, vaste initiële bronpolygonen
- Korte tijd `T=0.009` met `Δt=0.003` en controle `Δt=0.0015` bij `48^3`

## Vier cases per geometrie

1. `free_knot`: trefoil zonder achtergrond
2. `background_only`: eigenbeweging van de gesloten verticale achtergrondlus
3. `coupled`: **volledig tweezijdige Euler-terugkoppeling**
4. `frozen_background_diagnostic`: niet-Euler éénrichtingscontrole;
   uitdrukkelijk uitgesloten van evenwichtscertificering

In `Gate2_Coupled_Trefoil_Grid_v0.1.0-outputs/` staan per seed en rooster
JSON-metingen, `spatial_holdout.csv`, `G2_ASSESSMENT.json`, bronhashes,
de tijdstapverfijning en beperkte circulatiegevoeligheidstests.

## Zelf experimenteren

```
py src\euler_coupled.py --seed T_2_3_B1600_N512 --n 48 --steps 3 --gamma-bg 0.05
py src\euler_coupled.py --seed T_3_2_B1600_N512 --n 48 --steps 3 --gamma-bg -0.05
```

**Geen van deze commando's is een niet-lineaire stationaire veldzoeker.**
De onafhankelijke convergentieanalyse kwalificeert de residumeting, niet
het bestaan van een stationaire oplossing. Later: een volledig variabele
relatieve-evenwichtszoeker plus meekomende materiële topologie-tracers.

Zie `docs/MATHEMATICS_AND_LIMITS.md` voor afleidingen, randvoorwaarden en
verboden fysische claims.

**Interpretatie van R*-tabellen:** de background-only- en coupled-runs
gebruiken verschillende optimale referentietranslaties. Gebruik voor het
bepalen van wederzijdse inductie de afzonderlijk berekende kruistermen
`direct_cross_rhs_*_rms` uit de JSON-bestanden; hun verschillen worden
met een regressietest gecontroleerd.
