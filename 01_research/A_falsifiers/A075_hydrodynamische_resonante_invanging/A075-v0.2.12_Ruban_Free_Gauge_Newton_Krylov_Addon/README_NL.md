# A075-v0.2.12 — Free Gauge-Fixed Newton–Krylov Equilibrium

**Status:** `DEVELOPMENT_ONLY / CONTINUUM_EQUILIBRIUM_UNRESOLVED / PHYSICAL_STABILITY_UNRESOLVED`

Nieuwe, zelfstandige additieve uitbreiding bovenop **A075-v0.2.11**. De originele **A007-v0.1.0** analytische `T(2,3)` seed en het ongewijzigde **A075-v0.2.9** filamentmodel worden SHA-256 gecontroleerd. Geen bestaande A075-versiemap, framework of wetenschappelijke gate wordt aangepast of gepromoveerd.

## Onderzoeksvraag

Kan de exacte A007 analytische Ruban-geometrie met **B0 = 77/500 = 0,154** worden vervormd tot een relatief-evenwicht van de geregulariseerde Ruban-filamentvergelijking, met onafhankelijke verplaatsing van alle filamentpunten in twee normale richtingen?

Dit is *geen* volledige driedimensionale Euler-stroming en *geen* reconstructie van Rubans onbekende beginverstoringen. De dimensieloze parameters blijven `R0=1`, `Gamma=2*pi`, `delta=1/20`, `Lambda=7/5+ln(200)/2` en `tilde_Lambda0/2=(7/5-ln2/2)/2`.

## Verschil met v0.2.11

- **Geen beperkte Fourier-vormfamilie meer.** Bij N collocatiepunten zijn er 2N onafhankelijke normale vormcoördinaten, samen met onbekenden U en Omega.
- **Lokale parameter-gauge:** een vaste normale grafiek over de broncurve; de raaklijncomponent van de geïnduceerde beweging wordt met de actuele raaklijn verwijderd.
- **Axiale symmetrie-gauges:** twee orthogonale fasevoorwaarden fixeren translatie langs z en rotatie om z. Dit is *geen* volledige zes-vrijheidsgraden Euclidische gauge en geen bewijs van afwezigheid van andere nulmoden.
- **Jacobian-free Newton–Krylov:** GMRES (Generalized Minimal Residual) op eindige-differentie Jacobiaan-vectorproducten; een rechterpreconditioner beïnvloedt alleen de iteratie, niet het dynamische model. Backtracking weigert ontoelaatbare curves.
- **Vervolg op hogere resoluties:** spectrale interpolatie van normale verplaatsingen, gevolgd door nieuwe onafhankelijke residuberekening op 2N punten vóór optimalisatie.
- **Onafhankelijke regularisatiecontrole:** periodieke trapezoïdale versus segment-midpoint Biot–Savart-kwadratuur; optioneel Numba, met elke run een pariteitscontrole tegen de pure NumPy-bron.

## Installatie Windows

Pak deze ZIP **naast**, niet bovenop, de bestaande A075-v0.2.11 en A075-v0.2.9 mappen uit. Gebruik Python 3.10+ en een eigen virtuele omgeving:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install "numba>=0.61,<1"
run_all.cmd SELFTEST
run_all.cmd VERIFY
```

Numba is optioneel; zonder Numba wordt automatisch de tragere NumPy-referentie gebruikt. De numpy/scipy-versies moeten door je lokale Numba-versie worden ondersteund.

### Snelle studie

```bat
run_all.cmd GAUGE_NEWTON --n-levels 64,128 --max-newton 12 --run-id LOCAL_GAUGE_001
```

### Onafhankelijke vervolgstudie (rekentijd-intensiever)

```bat
run_all.cmd CONTINUE --n-levels 128,256,512,1024 --max-newton 14 --allow-expensive --run-id LOCAL_T23_CONTINUE_001
```

**Elke `run-id` is create-only.** Voer nooit een tweede run uit met dezelfde naam; de software weigert overschrijven. De source-only map bevat geen eerder uitgevoerde resultaten; deze zitten in het afzonderlijke outputarchief.

## Reeds uitgevoerde pilot (2026-10-30)

| N | vrij residu (trapezoid) | onveranderde vorm op 2N | midpoint op N | midpoint op 2N |
|---:|---:|---:|---:|---:|
| 128 | 2.01682722e-9 | 1.37182231e-2 | 4.03148192e-2 | 5.68730512e-3 |
| 256 | 1.39509750e-6 | 1.21221585e-3 | 1.94534602e-2 | 4.37148821e-3 |
| 512 | 8.05081964e-7 | 6.42963929e-6 | 5.54054364e-3 | 1.38242244e-3 |
| 1024 | 8.02045207e-7 | 8.02047738e-7 | 1.38805765e-3 | 3.47013941e-4 |

Alle waarden zijn residuen van het **geregulariseerde filamentmodel**, geen fysische stabiliteitsindicatoren. Op N=512 en N=1024 stopte Newton door een lijnzoek-blokkade; *optimizer success* is daar dus niet toegekend. `segment/delta` bij N=1024 is 0,2876, groter dan de conservatieve screen van 0,25. De onafhankelijke midpointresidu's zijn nog niet klein genoeg voor modeloverstijgende certificatie.

Bij N=128 is het numerieke **finite-N residual** onder 1e-8 gekomen; dit betekent uitsluitend een kandidaat-oplossing van de specifieke eindig gediscretiseerde vergelijkingen. Omdat de vaste vorm bij N=256 nog 0,0137 residu heeft, is deze kandidaat onvoldoende convergent.

## Outputstructuur

```text
A075_Hydrodynamische_Resonante_Invanging_v0.2.12-outputs/
  <run-id>/
    RUN_CONFIG.json
    RE_N128_GAUGE_FIXED.npz                 # reeks N, iedere met eigen XYZ en normale verplaatsingen
    NEWTON_HISTORY_N128.json                # alle Newton-stappen
    EQUILIBRIUM_CONVERGENCE.csv
    SCIENTIFIC_ASSESSMENT.json
    FALSIFIER_REPORT.md
    A075-v0.2.12_FALSIFIER_REPORT.pdf
    MANIFEST_SHA256.json
../A075_Hydrodynamische_Resonante_Invanging_v0.2.12_<run-id>_outputs.zip
../A075_Hydrodynamische_Resonante_Invanging_v0.2.12_<run-id>_outputs.zip.sha256
```

## Gates en stopregels

1. **G0 bronidentiteit:** A007 2048 bronbytes én originele A075-v0.2.9 filamentsolver moeten hun vastgepinde SHA-256 hebben. Bij mismatch weigeren.
2. **G1 numerieke consistentie:** alle residuen en geometrieën eindig, normale referentiegauge van rang twee, snelle backend vergeleken met de originele onafhankelijk geïmplementeerde kwadratuur.
3. **G2 evenwicht:** minimaal drie kerngeresolveerde niveaus, raaklijnparameter-invariantie, nulresidu met schaling tot truncatiefout, onafhankelijk midpoint/trapezoid-vergelijkbare uitkomsten. Tot die tijd `UNRESOLVED`.
4. **G3 stabiliteit:** linearisatie pas rond onafhankelijk gevalideerde evenwichten; eigenmoden, symmetriemoden, resolutieconvergentie. **Niet uitgevoerd in deze versie**.
5. **G4 fysische Euler-vorm:** gescheiden A075 eindige-kerntests, geometrie- en domeinconvergentie. **Niet uitgevoerd**.

De getalsmatige waarde 0,154 is de *gerapporteerde paperparameter*, geen bewezen optimale verhouding of natuurconstante. Alle modelparameters zijn dimensieloos. A007 is een analytische reconstructie, niet de originele simulatiecoördinaten.

## Referenties

V. P. Ruban, "Long-lived quantum vortex knots," *JETP Letters* 107 (2018), DOI: 10.1134/S0021364018050120.

Projectbronnen: bevroren A007-seed, A075-v0.2.9 bronmanifest en vergelijking-(9) software, A075-v0.2.11 numerieke trapezoïde/midpoint implementaties.

## Compatibiliteit van behouden oudere code

`ruban_equilibrium/runner.py`, `qualification.py`, `core.py`, `full_spectrum.py` en `high_order.py` zijn de bestaande v0.2.10/v0.2.11 implementaties die uit de vorige bronrelease zijn overgenomen. Het nieuwe, ondersteunde v0.2.12 commando gebruikt uitsluitend `gauge_runner.py` plus `free_gauge_nk.py`; voer de oudere module-entrypoints niet als v0.2.12 studie uit.
