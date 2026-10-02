# VortexLab v7.6.15 — SPEC CLOCK benchmark-verdictpersistentie

## Aanleiding

Een voltooide v7.6.13/v7.6.14 benchmark exporteerde correct:

- `ENGINE=PASS`
- `RESEARCH_PROXY=FAIL`
- tien geldige scenarioresultaten

Na voltooiing zette de benchmark de oorspronkelijke gebruikersconfiguratie veilig terug naar `tPhys=0`. Die restore liep via `resetState()`, waardoor de handmatige fase-nullreferentie terecht werd gewist. `resetSpecClockRuntime()` plaatste vervolgens de generieke runtime-status:

> WACHT OP DETERMINISTISCHE VELDSAMPLE · state-reset · fase-referentie opnieuw vereist.

Die tekst beschreef alleen de **teruggezette handmatige sessie**, maar overschreef visueel het reeds berekende benchmarkverdict. Daardoor leek een voltooide benchmark ten onrechte vastgelopen of ongeldig.

## Correctie in v7.6.15

1. Het ENGINE- en RESEARCH-PROXY-verdict wordt vóór `restoreConfiguration()` persistent opgeslagen in `LastSpecClockBenchmarkSummary`.
2. Na de veilige restore toont het SPEC CLOCK-paneel expliciet:
   - benchmark voltooid;
   - ENGINE-verdict;
   - RESEARCH-PROXY-verdict;
   - benchmarkresultaten blijven geldig;
   - alleen de teruggezette handmatige sessie vereist een nieuwe kalibratie.
3. De snelle SPEC CLOCK-overlay neemt dezelfde status automatisch over.
4. Een zichtbare simulatorbanner meldt het eindverdict direct na voltooiing.
5. Bij een nieuwe benchmark wordt de vorige persistente samenvatting gewist.
6. Ook een handmatig afgebroken benchmark krijgt een afzonderlijke restore-status.
7. Nieuwe regressietest `T0ac` controleert dat het verdict de sessierestore overleeft.

## Interpretatie van de aangeleverde benchmark

De aangeleverde benchmark is volledig uitgevoerd en niet vastgelopen:

- alle 10 runs zijn geldig;
- maximale eerste stap: `0.05 s`;
- afspeelinvariantie 1×/4×/16×: exact gelijk;
- cilinderhoogte 1 m versus 5 m: exact gelijk;
- BEM aan/uit bij uitgeschakelde bundel: exact gelijk;
- nuldriftstabiliteit: PASS;
- A/B-symmetrie: PASS;
- driftsweeptrend: PASS;
- fase-null versus formele veldbracket: FAIL.

De closure-gate vindt:

- faseproxy: `-1.6000277198249802e-9`;
- veldbracket: ongeveer `±2.22e-22`;
- schaalverhouding: `7.195073378084202e12`.

Dit verwerpt uitsluitend de huidige niet-canonieke faseproxyrealisatie. De ENGINE-uitkomst bevestigt dat de benchmarkrunner, tijdstapbootstrap, playback-invariantie en volume/BEM-negatieve controles correct functioneren.

## Niet gewijzigd

- Biot–Savart- of LIA-dynamica;
- CFL-formule en 50 ms SPEC CLOCK-cap;
- benchmarkscenario's en toleranties;
- fase-nullformule;
- SST/CANON-parameters;
- vierpaneel-layout en RUN-dropdown.
