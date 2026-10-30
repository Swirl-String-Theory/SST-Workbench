# A075-v0.2.11 — Ruban Relative Equilibrium & Full Finite-N Linear Spectrum

**Wetenschappelijke status** `DEVELOPMENT_ONLY / RELATIVE_EQUILIBRIUM_UNRESOLVED / CONTINUUM_SPECTRUM_UNRESOLVED / PHYSICAL_STABILITY_UNRESOLVED`.

Dit is een **standalone, additieve A075+A007 onderzoeksuitbreiding** van de bestaande A075-v0.2.10 addon. Geen inplace patch, geen volledige A075 Framework v1.1.0-release en geen modificatie van eerdere projecten. De oude A075-v0.2.9 operator wordt ongewijzigd als byte-gepinde bronreferentie meegeleverd; de nieuwe numerieke operator is onafhankelijk.

## Installatie onder Windows

Pak de bron-ZIP uit onder
`C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A075_hydrodynamische_resonante_invanging\`

De nieuwe submap is `A075-v0.2.11_Ruban_Equilibrium_Spectrum_Addon`; `A075-v0.2.9` en `A075-v0.2.10_Ruban_Equilibrium_Addon` blijven intact.

```bat
cd C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A075_hydrodynamische_resonante_invanging\A075-v0.2.11_Ruban_Equilibrium_Spectrum_Addon
python -m pip install -r requirements.txt
run_all.cmd SELFTEST
run_all.cmd VERIFY
run_all.cmd EQUILIBRIUM --n-levels 128,256 --harmonics 3 --run-id LOCAL_RE_001 --allow-expensive
run_all.cmd QUALIFY --n-levels 64,96 --harmonics 3 --run-id LOCAL_MATRIX_001
```

Een zwaardere, onafhankelijke convergentiecontrole:

```bat
run_all.cmd EQUILIBRIUM --n-levels 512,1024 --harmonics 3 --run-id LOCAL_HIGH_001 --allow-expensive
run_all.cmd EQUILIBRIUM --n-levels 2048 --harmonics 3 --run-id LOCAL_CORE_001 --allow-expensive
```

Andere gevallen via `--b0 0.152` of `--harmonics 4` en een **nieuwe** run-id. Geen auto full-campaign of scan van andere torusknopen.

## Formele onderzoeksvraag

Is er voor Rubans T(2,3), B0=77/500, delta=1/20 en Lambda=7/5+ln(200)/2 een convergerende **relatief-stationaire** filamentvorm en een fysisch interpreteerbaar lineair stabiliteitsspectrum?

De optimizer zoekt de beste radiale en verticale correcties binnen de begrensde `q=3`-symmetrische harmonische familie, met behoud van oorspronkelijke p=2, q=3 windingen en van de grondmodus B0. Dit is **niet** een onbeperkte shape-optimalisatie. De A007-coördinaten zijn SHA256-geverifieerd en vormen bij precies B0=77/500 de initiële collocatietoestand. Voor andere B0 worden nieuwe analytische torussen gebruikt, niet foutief aangeduid als A007-data.

Het discrete veld gebruikt Ruban Eq.9, met onafhankelijke midsegment-/periodieke trapeziumkwadratuur en spectrale krommingsafgeleiden. De `2N×2N` Jacobiaan wordt opgebouwd met gecentreerde differenties op **alle** N maal twee lokale normaalvrijheidsgraden. Vaste U, Omega en de basis-tangentiële gaugesnelheid worden in de coroterende linearisatie gebruikt. **Dat is een complete matrix van deze gediscretiseerde normale operator, geen compleet continue spectrum.** De eigenwaarden zijn niet geldig als fysische stabiliteitsgroeisnelheden zolang het basis-evenwicht niet is aangetoond.

## Huidige echte runs

- `T23_FULL_NORMAL_SPECTRUM_N64_N96_001`: N64 en N96, 128 en 192 eigenwaarden, matrices op h en h/2, gerapporteerde convergentiediagnostiek.
- `T23_EQUILIBRIUM_N128_N256_001`: hogere ruimtelijke controle.
- `T23_EQUILIBRIUM_N512_N1024_001`: near-core resolutiecheck.
- `T23_EQUILIBRIUM_N2048_001`: test met max.segment/delta ~0.144. Ook hier blijft residu ~0.051521 en is er dus geen gevonden exact evenwicht binnen de gekozen vormfamilie.

De eerste `N32/N48` rooktest was een voorbereidende matrixcheck; het uiteindelijke rapport baseert zich op N64..2048. Alle berekende standaardresultaten zijn diagnostisch; geen enkele officiële A075-Framework-gate krijgt PASS.

## Belangrijke limieten

1. Gebruikte vormbasis beperkt tot extra radiaal-/hoogte-harmonischen q*2,...,q*(H+1). Mogelijke asymmetrische of niet-toroïdale evenwichten kunnen ontbreken.
2. Bij N64 en N96 is delta=0.05 sterk ondergeresolveerd: de volledige discrete spectra zijn exploratief, **geen** betrouwbare continue spectrumbenadering.
3. Zelfs bij N2048 is de gevonden eindresidu niet nul; rasterconvergentie van een **niet-nul residu** bewijst geen evenwicht.
4. De oorspronkelijke Ruban-verstoring en auteursdiscretisatie zijn onbekend/niet hersteld. De lange overlevingstijd t=320 is niet gereproduceerd.
5. De exacte torusknoop in een volledige 3D Euler-stroming, finite-core-topologie en lange-tijdstabiliteit worden niet beoordeeld.
6. `--max-nfev` is een optimalisatiebudget, geen garantie op convergentie. Voor een *compleet* fysisch spectrum moet eerst de basisvorm geconvergeerd zijn, en daarna eigenwaardeconvergentie en gauge/constraint-validatie worden aangetoond.

## Output

`./A075_Hydrodynamische_Resonante_Invanging_v0.2.11-outputs/<run-id>/` bevat `RUN_CONFIG.json`, `FULL_RESULTS.json`, `EQUILIBRIUM_CONVERGENCE.csv`, per-N `FULL_DISCRETE_JACOBIAN_N*.npz`, `FULL_DISCRETE_SPECTRUM_N*.json` (indien gevraagd), seedvormen, `SCIENTIFIC_ASSESSMENT.json`, `FALSIFIER_REPORT.md/.pdf`, en `MANIFEST_SHA256.json`.

In de bovenliggende familiemap wordt per run `A075_Hydrodynamische_Resonante_Invanging_v0.2.11_<run-id>_outputs.zip` met `.sha256` aangemaakt. Archieven en bestaande run-IDs worden nooit overschreven.

## Methodische referenties

- V. P. Ruban, *Long-lived quantum vortex knots*, JETP Letters **107** (2018), 307–311, https://doi.org/10.1134/S0021364018050120.
- V. P. Ruban, *Quasi-stable configurations of torus vortex knots and links*, JETP **127** (2018), 581–586, https://doi.org/10.1134/S106377611809008X.
- J. P. Boyd, *Chebyshev and Fourier Spectral Methods*, Dover (2001), https://store.doverpublications.com/products/9780486411835.
