# VortexLab v7.6.24c — benchmark-gate stabilisatie

**Basis:** v7.6.24b  
**Type:** infrastructuur-/testharnasrelease  
**Solverfysica:** ongewijzigd

## Doel

V7.6.24c corrigeert de beoordelingslaag vóór de inhoudelijke roadmap wordt hervat. De release wijzigt geen Biot–Savartwet, integrator, Swirl-Clockformule, kandidaat-κ, reachschatter of knotgeometrie.

De verwachte wetenschappelijke status blijft:

\[
\mathrm{ENGINE}=\mathrm{PASS}\quad	ext{na een nieuwe volledige run,}
\]

\[
\mathrm{RESEARCH}=\mathrm{FAIL}.
\]

Dat is geen resultaatgerichte aanpassing: de softwarelaag moet correct classificeren, terwijl de huidige proxyfamilie inhoudelijk verworpen blijft.

## Testcorrecties

### D2 — mutual-linearity en all-on-proxy

De directe mutual-linearity gebruikt nu een zero-safe mixed tolerance:

\[
|\epsilon|\le 10^{-18}+10^{-5}\,\mathrm{scale}.
\]

De all-on legacy-phaseproxy wordt alleen gecontroleerd voor niet-holdoutscenario’s waarin deze projectie toepasselijk en eindig is. Intrinsieke projection-null-holdouts zijn expliciet `N/A` voor deze subtest.

Replay op de echte v7.6.24b-export:

- worst mixed score: circa \(1.00	imes10^{-4}\);
- 29 toepasselijke proxysnapshots;
- maximale all-on-fout: circa \(2.45	imes10^{-15}\).

Daarmee hoort D2 `PASS` te zijn.

### D4 — cyclic-index-invariantie

D4 wordt niet langer beslist door alleen de legacy lab-z-scalar. De gate gebruikt nu:

- de volledige intrinsieke \(oldsymbol\Omega\)-vector;
- \(\Omega_\parallel\);
- afzonderlijke ISO- en mutual-mixed tolerances;
- projection-null als geldige, niet-informatieve toestand.

De legacy lab-z-relatieve fout blijft uitsluitend diagnostisch.

### D6 — normalisatiepipeline

Alle zeven normalisaties moeten voor alle snapshots eindig blijven. De `ISO_DYNAMIC`-match met de oude phase-nullproxy wordt alleen geëist voor toepasselijke niet-holdouts. Intrinsieke holdouts worden niet meer gedwongen een niet-informatieve lab-z-projectie te reproduceren.

Replay op v7.6.24b:

- 49/49 snapshots hebben eindige normalisaties;
- 29 toepasselijke proxysnapshots;
- maximale matchfout: circa \(2.45	imes10^{-15}\).

Daarmee hoort D6 `PASS` te zijn.

### R22 — topology-specifieke opsplitsing

R22 is vervangen door:

- **R22a:** alleen de trefoil-resolutieladder versus \(\operatorname{Rop}_{m diam}(3_1)=16.371637\);
- **R22b:** iedere ideal holdout gebruikt uitsluitend zijn eigen Gilbert-`L/D`-metadata;
- **R22c:** Fourierembeddings zonder onafhankelijk toegewezen fysieke diameter krijgen `N/A`.

R22a blijft terecht `FAIL`: de trefoilmismatch bij \(N=768\) is circa \(5.375\%\). Reach-afhankelijke κ-factoren blijven dus geblokkeerd tot v7.6.25.

## Benchmark-performance

Beide automatische benchmarkrunners zetten tijdelijk:

```text
tracerCount = 0
showTracers = false
showStreamlines = false
showPotentialFlow = false
```

Hierdoor vervalt de passieve particle-integratie en cosmetische flowrendering tijdens de test. De oorspronkelijke waarden worden exact hersteld bij:

- normale voltooiing;
- handmatige stop;
- setupfout;
- checkpointfout.

ModelLog registreert `benchmark-visual-suppression` en `benchmark-visual-restore`.

Nieuwe ENGINE-controles:

- `D14` voor de 49-snapshot decomposition-run;
- `visual-isolation` voor de gewone 10-runbenchmark.

## Schema

De decomposition-export is verhoogd naar:

```text
vortexlab-spec-clock-proxy-decomposition/1.9
```

## Roadmap

Na deze stabilisatie blijft de volgorde:

1. **v7.6.25:** continue DCSD/reach-solver;
2. **v7.6.26:** signed lokale Swirl-Clockroute;
3. afstand/oriëntatie/multipool;
4. materiaalframe en velocity-gradienttensor;
5. confirmatoire v7.7.0-mijlpaal.

## Validatie

- JavaScript-syntax: PASS;
- diff past schoon op v7.6.24b;
- D2-replay: PASS;
- D6-replay: PASS;
- R22a-replay: FAIL zoals wetenschappelijk verwacht;
- alle 20 scenario’s, 10 holdouts en 49 snapshots blijven behouden;
- solver- en kandidaatregisters zijn niet gewijzigd.

Een nieuwe lokale 49-snapshotrun is vereist om de nieuwe intrinsieke D4-metrieken en het definitieve v7.6.24c-ENGINE-verdict te meten.
