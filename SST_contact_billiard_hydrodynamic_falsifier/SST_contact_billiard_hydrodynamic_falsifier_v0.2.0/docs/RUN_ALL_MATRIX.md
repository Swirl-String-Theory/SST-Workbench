# RUN_ALL research matrix

`RUN_ALL_MAX_RESEARCH.cmd` is de Windows-orchestrator voor de volledige falsificatiecampagne. De tweede laag, `scripts/run_all_research.py`, maakt een deterministisch, hervatbaar experimentenplan en behandelt een wetenschappelijke gate failure als geldig resultaat.

## Presets

| Preset | Fourier source samples | Hoofd-geometrie | Hoofd-hydrodynamica | Contactconvergentie | Doel |
|---|---:|---:|---:|---|---|
| `quick` | 4096 | 256 | 64 | 128–256 | installatie- en pipelinecontrole |
| `full` | 8192 | 512 | 96 | 128–768 | normale onderzoekscampagne |
| `max` | 16384 | 768 | 128 | 128–1536 | standaard maximale evidence matrix |
| `extreme` | 32768 | 1024 | 192 | 192–3072 | langdurige asymptotische/stability campagne |

De hydrodynamische hoofd-sweep gebruikt in `max`

\[
\frac{a}{\Delta}
\in
\{0.05,0.075,0.10,0.15,0.20,0.30,0.40,0.50,0.65,0.80,1.00,1.25,1.50\},
\]

voor `full`, `local` en `nonlocal` interacties. De `extreme`-sweep vergroot dit bereik tot

\[
0.03\leq \frac{a}{\Delta}\leq 2.00.
\]

## Experimentgroepen

1. Database-audit en SHA-256-provenance.
2. Contactmap- en 9-billiard-resolutieladder.
3. Sensitiviteit voor de lokale exclusion fraction.
4. Invariantie onder cyclische parameter shift, oriëntatiereversal, rigide beweging en uniforme schaal.
5. Deterministische ruisperturbaties van de centerline.
6. Negatieve controles: analytische torustrefoil, cirkel en figure-eight.
7. Volledige finite-core hydrodynamische kernsweep.
8. Hydrodynamische resolutieladder.
9. Sensitiviteit voor de `local_band`-splitsing.
10. SI-schaalguard bij \(0.5r_c\), \(r_c\) en \(2r_c\).
11. Hydrodynamische oriëntatie- en rigid-motion-invariantie.

## Hervatten

De standaard CMD-call gebruikt `--resume`. Bij herstart wordt de lexicografisch nieuwste runmap voor dezelfde preset hervat en worden stappen met een geldig `summary.json` of `convergence.json` overgeslagen.

Een nieuwe run forceren:

```bat
RUN_ALL_MAX_RESEARCH.cmd max new
```

## Logging

Iedere stap krijgt direct bij start een niet-lege log in

```text
outputs/run_all/<preset>/<UTC-run-id>/logs/
```

De commandoregel en starttijd worden vóór de numerieke berekening geschreven. Eventuele subprocess-output wordt live naar terminal én log gestreamd.

## Resultaten

De runmap bevat minimaal:

```text
campaign_plan.json
progress.json
run_manifest.json
research_index.csv
gate_matrix.csv
robustness_summary.json
RESEARCH_REPORT.md
database_audit.json
campaigns/**/summary.json
```

Na een voltooide run wordt daarnaast een ZIP en `.sha256` naast de runmap geplaatst.

## Computationele grens

De Hamiltoniaanse finite-difference-gradiënt evalueert voor ieder centerlinepunt drie centrale verschillen, waarbij iedere energie-evaluatie alle segmentparen bevat. De referentie-implementatie schaalt daarom ongeveer als

\[
T(N)\sim O(N^3).
\]

De `max`- en `extreme`-presets kunnen vele uren tot langer dan een dag kosten, afhankelijk van CPU, BLAS en filesystem. Meer samples verminderen discretisatiefouten, maar lossen de modelbeperking niet op dat slechts één Rosenhead-type finite-core-kernel wordt getest.
