# A075 → A026 Euler Trajectory Exporter — additieve patch v0.1.0

**Status:** `DEVELOPMENT_ONLY / FORMAT_AND_NUMERICAL_SMOKE_TESTED / PHYSICAL_MEMORY_UNRESOLVED`.

Dit is een **losstaande exporter**. Hij wijzigt **geen** bestaande A075/A026-bron, frozen release, `run_all.cmd`, registry of framework.

## Bronpinnen

Deze patch gebruikt precies de gecontroleerde bestanden uit **A075-v0.2.9**:

- `experiment/euler3d.py` SHA-256 `e66cb8430d70e2738f6ddb2505d446c47b2a11cb71d9f6310ebbb2321748a063`.
- `experiment/ruban.py` SHA-256 `6c402e8f9928556f3593447ef85f7874d23f472f21d689261a30bafa623642f6`.

Veranderde broncode leidt tot `A075_SOURCE_DRIFT` en exit 2. Gebruik dus niet blind A075-v0.2.10 of v0.2.12. Die add-ons hebben mogelijk andere bronbestanden.

De Ruban-seed wordt **rechtstreeks uit de bestaande** `inputs/ruban_t23/RUBAN_T23_B0_0p154_N2048_EQUAL_ARCLENGTH.xyz` geladen, inclusief controle met `SEED_MANIFEST.json`. Hij zit bewust niet in deze patch.

## Benodigd

- Python 3.10+ op Windows, `numpy`, `scipy`, `pytest`.
- Je **bestaande volledige map A075-v0.2.9**, inclusief de twee genoemde .py-bestanden én `inputs/ruban_t23/...`.
- De bestaande `A026_HiddenStateMemory_SIDECAR_v0.1.0` voor verdere beoordeling.

Uitpakken in een aparte map naar keuze; deze patch NIET over bestaande A075-bestanden kopiëren.

Installatie: `py -3 -m pip install -r requirements.txt`.

## Command: eerst smoke

In de uitgepakte patchmap in `cmd.exe`:

```cmd
run_a026_export.cmd "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A075_Hydrodynamische_Resonante_Invanging\A075-v0.2.9" --mode ruban --trials 4 --samples 12 --grid 16 --final-time 0.04 --dt 0.01
```

Dit produceert **4 × 12** meetpunten voor softwarecontrole; **niet** acceptabel voor de A026 intake (die eist ≥80 trajecten). De gebruiker kan het pad van zijn eigen A075-folder invullen.

## Command: genereren voor de bestaande A026 intake

```cmd
run_a026_export.cmd "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A075_Hydrodynamische_Resonante_Invanging\A075-v0.2.9" --mode ruban --trials 80 --samples 16 --grid 32 --sigma 0.5 --final-time 0.10 --dt 0.01 --perturbation 0.02 --master-seed 2601029
```

Dit is **alleen een formaat- en methodecampagne**. De Ruban-trefoil heeft `r_minor=0.154` en bij box 10, grid 32 slechts 0.49 cellen per kleine radius. Zelfs bij grid 80 is dit 1.232 cellen per radius, onvoldoende voor gecertificeerde knoopdynamica.

80 trajecten worden als **80 aparte 3D Euler-realisaties** berekend. Elke realisatie heeft een eigen `SeedSequence` en een onafhankelijk glad, solenoïdaal achtergrondperturbatieveld. Geen tijdsegmenten van één run worden vermomd als onafhankelijke experimenten.

`q_m` is de ongewrapte coördinaat van één *materiële passieve tracer* die aanvankelijk op een punt van de mathematische knoopseed ligt; `qdot_m_s` is zijn actuele lokale Euler-snelheidscomponent op hetzelfde tijdstip, uit de opgeloste veldtoestand. Dit is **geen getrackte vortex-core centerline, geen knoopcentroid, geen faseklok**.

Het traject wordt tegelijk met het Euler-veld geïntegreerd met vierde-orde Runge–Kutta en gedeelde veldstadia. Alle trajecten eindigen op dezelfde absolute simulatie-eindtijd; de tussentijdse sampletijden zijn uniform. Het veld is periodiek, inviscide, onversterkt en gebruikt A075's de-aliasing.

## Belangrijk over SI-schaal

A075 heeft dimensieloze invoer. De exporter past een expliciete Euler-similariteitstransformatie toe:

- `--length-unit-m 1.0` (standaard), `--speed-unit-m-s 1.0` (standaard).
- Dan zijn `times_s` in s, `q_m` in m en `qdot_m_s` in m/s en kan de **bestaande** A026-analysator de zeer kleine varianties numeriek verwerken.
- De standaardlengte 1 m is **geen** fit aan de SST Canon en mag niet als fysieke kernradius worden beschreven.
- Je kunt `--length-unit-m 1.40897017e-15 --speed-unit-m-s 1.09384563e6` opgeven, maar **A026 v0.1.0 weigert kleine featurevarianties onder 1e-14 in absolute SI-eenheden**. Voor Canon-schaling is dus eerst een nieuwe, dimensioneel genormaliseerde A026-analysator noodzakelijk; verander niet stilzwijgend de units om deze weigering te omzeilen.

## A026 gebruiken

De exporter print het nieuwe uitvoerpad. Default:

`../A075_A026_EulerTrajectories_v0.1.0-outputs/<UTC-RUN-ID>/independent_trajectories.npz`

Controleer het bestand:

```cmd
py -3 validate_a026_npz.py "C:\...\independent_trajectories.npz"
```

Daarna vanuit de **A026 sidecar-map**:

```cmd
run_all.cmd EULER "C:\...\independent_trajectories.npz"
```

A026 schrijft een diagnostisch rapport en keert bewust terug met **exitcode 3** (`NOT_CERTIFIED`) bij echte Euler-data zonder volledige wetenschappelijke gatekwalificatie. Format-PASS of eventueel lagere prediction-RMSE is GEEN SST-claim.

## Andere bestaande A075-modi

`--mode legacy_t23` gebruikt A075's analytische controle-trefoil met `B0=0.32`, zonder Ruban-ingangseed. Goed voor installatiecontrole.

`--mode coupled_ring_trefoil` gebruikt A075's historische `legacy_coupled` met **een gesloten ring plus een trefoil**, geen parallel wervelrooster. Het Euler-veld is wederzijds gekoppeld; de mode is niet geometrisch gematcht met Ruban en mag niet worden vergeleken alsof enkel achtergrondgeheugen verschilt.

## Uitvoergates

- `source_pin`: controle bij runtime.
- `format`: alleen ≥80 × ≥12 en metadata (plus `validate_a026_npz.py`).
- `spatial_convergence`, `temporal_convergence`, `core_convergence`, `domain_convergence`, `tracer_convergence`: **NOT_RUN**.
- `physical_background_filament_reaction`: **NOT_IMPLEMENTED** (er is geen parametrisch raster parallelle kernen in deze patch).
- `intrinsic_phase_clock`: **UNRESOLVED**.

De output registreert alle individuele seeds, energie-drifts, stap- en afwijsdiagnostieken plus inputbestands-hashes. Geen bestaande output wordt overschreven; elke run heeft een unieke uitvoermap.

## Referenties

```latex
\bibitem{Muruga2026}
L. Muruga, F. Ginot, S. A. M. Loos, and C. Bechinger (2026),
``The extraction of work from hidden degrees of freedom,''
Nature Physics, doi:10.1038/s41567-026-03442-w.

\bibitem{Mori1965}
H. Mori (1965), ``Transport, collective motion, and Brownian motion,''
Progress of Theoretical Physics 33, 423--455,
doi:10.1143/PTP.33.423.
```
