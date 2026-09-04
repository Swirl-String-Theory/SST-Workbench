# SST Contact–Billiard–Hydrodynamic Falsifier v0.2.0

Zelf-contained Python research harness voor de keten

\[
\boxed{
\text{contactmap}
\rightarrow
\text{9-billiard}
\rightarrow
\text{geometrische krachtbalans}
\rightarrow
\text{onafhankelijke finite-core hydrodynamische test}
}
\]

Het pakket is ontworpen voor **SST-Workbench** en accepteert zowel Brian Gilberts
`ideal.txt`/`ideal_favorites.txt` als KnotPlot/Ridgerunner XYZ-, TXT- en
ééncomponent-VECT-bestanden.

## Wetenschappelijke status

Dit pakket probeert de route te **falsifiëren**, niet te bevestigen. Een volledige
`PASS` betekent uitsluitend dat de ingevoerde geometrie niet is verworpen door de
geconfigureerde numerieke gates. Het bewijst geen SST-deeltje en geen elektronmodel.

De bron voor de contactmap, gesloten 9-billiard en hoek-/krachtcompatibiliteit is
Mathias Carlens EPFL-thesis over ideale knopen. De thesis presenteert de 9-billiard
als een numerieke ontdekking en merkt expliciet op dat de krachtcompatibiliteit nog
niet uit ropelength-minimalisatie is afgeleid. De hydrodynamische laag in dit pakket
is daarom strikt onafhankelijk gehouden van de contactfit.

## H0–H8 gates

| Gate | Centrale test | Passbetekenis |
|---|---|---|
| **H0** | invoer, booglengtediscretisatie en bronmetadata | numerieke basis en gedeclareerde \(L,D\)-schaal zijn consistent |
| **H1** | twee dubbel-kritische contacttakken | contactmap is voldoende compleet en orthogonaal |
| **H2** | winding en inverse relatie | de takken gedragen zich als graad-één inverse kaarten |
| **H3** | gepaarde primitieve 9-orbit | beide inverse takken sluiten, hebben geen lagere periode en leveren dezelfde orbitset |
| **H4** | Carlen-compatibiliteit | beide scalaire actie-reactierelaties sluiten |
| **H5** | regularized Biot–Savart relative equilibrium | de vorm beweegt hoofdzakelijk rigide |
| **H6** | Hamiltoniaanse energiegradiënt | \(\delta H_a/\delta\mathbf X\) volgt \(-\kappa\mathbf n\) met positieve, bijna constante spanning |
| **H7** | finite-core sweep | H5 en H6 blijven geldig over voldoende \(a/\Delta\)-waarden |
| **H8** | niet-lokale guard | een nonlocal-only interactie reproduceert de contactkracht niet triviaal via lokale inductie |

Zie `docs/GATES.md` voor exacte thresholds en blockerlogica.

## Windows quick start

```bat
py -3 -m venv .venv
.venv\Scripts\activate
py -3 -m pip install -e ".[test]" --no-build-isolation
py -3 -m pytest
```

De volledige Brian-Gilbert-catalogus is nu meegeleverd als:

```text
data\ideal_favorites.txt
```

De package registreert voor iedere campagne de database-SHA-256 en de bronmetadata. Voer een enkele trefoilcampagne uit:

```bat
RUN_GILBERT_TREFOIL.bat
```

Of als one-liner:

```bat
py -3 -m sstcbhf analyze --database data\ideal_favorites.txt --id 3:1:1 --samples 384 --hydro-samples 96 --hydro-interactions full nonlocal --core-ratios 0.10 0.20 0.35 0.50 0.75 1.00 --physical-thickness 1.40897017e-15 --out outputs\gilbert_3_1_contact_hydro
```

Een Ridgerunner-polishbestand analyseren:

```bat
RUN_RIDGERUNNER_POLISH.bat "C:\workspace\projects\SST-Workbench\KnotPlot\ridgerunner\out\ideal_3_1_1\YOUR_POLISH.txt"
```

Equivalent via de CLI:

```bat
py -3 -m sstcbhf analyze --input C:\workspace\projects\SST-Workbench\KnotPlot\ridgerunner\out\ideal_3_1_1\YOUR_POLISH.txt --samples 384 --hydro-samples 96 --out outputs\ridgerunner_3_1_contact_hydro
```

De brongeometrie blijft autoritatief. De interne uniforme resampling is uitsluitend
voor afgeleiden, contacttracking en convergentiediagnostiek; het pakket schrijft de
resampled curve apart weg en overschrijft de invoer nooit. `--hydro-samples` staat
bewust lager dan `--samples`: de centrale finite-difference energiegradiënt schaalt in
de huidige referentie-implementatie ongeveer als \(O(N^3)\).


## Volledige RUN_ALL-researchmatrix

Start vanuit Windows CMD of door dubbelklikken:

```bat
RUN_ALL_MAX_RESEARCH.cmd
```

Standaard wordt preset `max` uitgevoerd. Andere niveaus:

```bat
RUN_ALL_MAX_RESEARCH.cmd quick
RUN_ALL_MAX_RESEARCH.cmd full
RUN_ALL_MAX_RESEARCH.cmd max
RUN_ALL_MAX_RESEARCH.cmd extreme

rem Forceer een nieuwe run in plaats van de laatste onvoltooide run te hervatten:
RUN_ALL_MAX_RESEARCH.cmd max new
```

De runner maakt automatisch een `.venv`, installeert de package, voert de tests uit en start daarna een hervatbare matrix met:

- contact- en 9-billiard-convergentie tot maximaal 1536 punten (`max`) of 3072 (`extreme`);
- exclusion-fraction-sensitiviteit;
- parameterisatie-, oriëntatie-, schaal- en rigid-motion-invariantietests;
- deterministische geometrische ruisperturbaties;
- negatieve controles voor een analytische torustrefoil, de cirkel en de figure-eight;
- een dichte finite-core-sweep met `full`, `local` en `nonlocal` interacties;
- hydrodynamische resolutie-, local-band- en fysieke-schaalsweeps;
- een gecombineerde `research_index.csv`, `gate_matrix.csv`, `RESEARCH_REPORT.md`, runmanifest en resultaten-ZIP.

Een wetenschappelijke `FAIL` is een geldig falsificatieresultaat en stopt de matrix niet. Alleen een software- of infrastructuurfout geeft een niet-nul exitcode. De presets `max` en vooral `extreme` kunnen op de huidige referentie-implementatie vele uren lopen, omdat de finite-difference energiegradiënt ongeveer als $O(N^3)$ schaalt. Alle stappen zijn deterministisch en `--resume` wordt standaard gebruikt.

De onderliggende runner kan ook direct worden aangeroepen:

```bat
.venv\Scripts\python.exe scripts\run_all_research.py --database data\ideal_favorites.txt --preset max --out-root outputs\run_all --resume
```

Voor alleen een controle van het geplande experiment, zonder numerieke campagnes:

```bat
.venv\Scripts\python.exe scripts\run_all_research.py --preset extreme --plan-only
```

## Negatieve controle

```bat
RUN_DEMO.bat
```

Dit gebruikt een gewone analytische torustrefoil, **niet** de ideale trefoil. De
verwachting is dat meerdere gates falen. Een demo die overal slaagt zou juist op een
te zwakke testketen wijzen.

## Convergentiecampagne

```bat
RUN_CONVERGENCE.bat
```

Dit berekent een ladder voor lengte, sampled thickness/reach, contactinversie en
9-billiard closure. Een enkele hoge-resolutierun is geen convergentiecertificaat.

## Outputstructuur

```text
outputs/<campaign>/
  summary.json
  gates.json
  manifest.json
  geometry/resampled_curve.xyz
  contact/contact_map.csv
  billiard/billiard9.json
  billiard/orbit9.xyz
  force/geometric_force_balance.csv
  hydrodynamics/core_sweep.csv
  hydrodynamics/fields.npz
  plots/*.png
```

`summary.json` bevat de SST-constanten, bronprovenance, SHA-256 van de
resampled geometrie, instellingen, alle metrics, gate-statussen en non-claims.

## Canonieke SST-normalisatie

```text
v_swirl  = 1.09384563e6 m s^-1
r_c      = 1.40897017e-15 m
rho_core = 3.8934358266918687e18 kg m^-3
rho_f    = 7.0e-7 kg m^-3
F_swirl_max = 29.053507 N
F_gr_max    = 3.02563e43 N
```

De standaardcirculatie is

\[
\Gamma_c=2\pi r_c\mathbf{v}_{\!\boldsymbol{\circlearrowleft}},
\]

en de geometrische thickness wordt standaard naar \(r_c\) geschaald. Deze mapping
is een expliciete SST-onderzoeksaanname, geen uitkomst van de knoopgeometrie.

## Belangrijkste beperkingen

- De contactextractor gebruikt een continue kubische centerline-interpolatie, maar
  is geen libbiarc-certificaat en geen exacte Ridgerunner-strutsolver.
- De sampled thickness is een DCSD/reach-proxy.
- De 9-billiard blijft numeriek totdat hij onder invoer-, parameter- en
  resolutieverfijning convergeert.
- De Rosenhead-type regularisatie is een filamentproxy voor een finite core, geen
  opgeloste 3D Euler-kern met expliciet drukveld en vorticiteitsprofiel.
- H6 gebruikt de Hamiltoniaanse variatiederivaat; de feitelijke vortexbeweging wordt
  afzonderlijk door Biot–Savart getest in H5.
- De local/nonlocal indexsplit van H8 is discretisatie-afhankelijk en moet zelf worden
  verfijnd.

Lees `docs/METHODS.md`, `docs/GATES.md` en `docs/KNOWN_LIMITATIONS.md` vóór een
fysische interpretatie.
