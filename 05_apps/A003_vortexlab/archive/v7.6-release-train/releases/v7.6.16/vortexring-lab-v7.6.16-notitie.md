# VortexLab v7.6.16 — proxy-decompositiebenchmark

**Parent:** v7.6.15  
**Base:** v7.5.3  
**Status:** geïmplementeerde Research-Track benchmark; strikt passief en niet-canoniek

## Doel

v7.6.16 ontleedt de bestaande

\[
\Delta\ln R_{AB}^{\mathrm{phase-null}}
\]

in vijf counterfactuale kanalen:

- `GEOM`: intrinsieke geometrische vervorming na rigid-poseverwijdering;
- `PARAM`: invloed van live nodeparametrisatie tegenover uniforme arclengthsampling;
- `ROT`: best-fit rigid-body-rotatie;
- `TRANS`: centroidtranslatie en eventuele translatielekkage;
- `MUTUAL_BS`: het direct door de andere drager geïnduceerde Biot–Savartveld.

Een zesde uitvoer, `RESIDUAL`, controleert de reconstructie. De benchmark introduceert geen nieuwe SST-overdrachtswet en past geen fitfactor toe.

## Starten

Kies in de header onder **RUN**:

> 🧬 SST CLOCK · proxy-decompositiebenchmark

Dezelfde runner kan ook worden gestart vanuit het SPEC CLOCK-paneel met **Run decompositie**.

De runner vervangt tijdelijk de actuele toestand, voert de analyse uit en zet daarna de oorspronkelijke configuratie veilig terug naar \(t=0\). Een nieuwe handmatige klokrun moet daarna opnieuw worden gekalibreerd.

## Uitgevoerde dynamische scenario’s

1. baseline, trefoil, \(v_{z,A}=+5\) mm/s en \(v_{z,B}=-5\) mm/s, \(N=128\);
2. static-null, beide opgelegde drifts nul, \(N=128\);
3. A/B-traversal-swap, \(N=128\);
4. dezelfde baseline op hogere vaste resolutie, \(N=192\).

Per scenario landt de solver exact op:

\[
t=0,\ 0.5,\ 1.0,\ 2.0,\ 3.0\ \mathrm{s}.
\]

Dit levert twintig passieve snapshots. De analyse wordt alleen op deze checkpoints uitgevoerd; er is geen feedback naar RK4, CFL, topology guard of filamentgeometrie.

## Snapshotinhoud

Per checkpoint worden gekopieerd en geëxporteerd:

- actuele geometrie en calibratiegeometrie;
- volledige, geïsoleerde en directe mutual snelheidsvelden;
- geometry- en parametergridhashes;
- segmentgewichten en segmentratio;
- centra en gewogen Kabsch-pose inclusief RMS en cyclic shift;
- \(\mathbf U\), volledige 3D \(\boldsymbol\Omega_{\mathrm{rigid}}\) en deformation residual voor full/iso/mutual;
- full/iso/mutual body-\(\Omega\) voor A en B;
- alle 32 counterfactualwaarden;
- Shapley-bijdragen voor raw mutual \(\Omega\), `deltaFrac` en \(\Delta\ln R\);
- afzonderlijke A- en B-attributies;
- reconstructieresidual, formele veldbracket en topology gap.

## Counterfactualconventie

De vijf toggles vormen alle \(2^5=32\) subsets. Voor elk kanaal wordt de Shapley-bijdrage berekend. Daardoor is het resultaat niet afhankelijk van een willekeurige volgorde van aftrekken.

Binnen iedere `GEOM`/`PARAM`-tak blijft de **all-on geïsoleerde** \(|\Omega|\)-normalisatie bevroren. Dit voorkomt kunstmatige singulariteiten wanneer een `ROT`- of `TRANS`-ablatie de geïsoleerde rigid-body-\(\Omega\) bijna nul maakt. Het all-on masker gebruikt actuele geometrie, live sampling, alle rigid- en translatiecomponenten en het directe mutual veld; dit masker moet de bestaande phase-nullproxy reproduceren.

## ENGINE-gates

- `D0 snapshot-purity`: \(Y\), \(t_{\rm phys}\) en calibratiereferenties zijn vóór en na analyse identiek;
- `D1 velocity-reconstruction`: \(\mathbf U+\boldsymbol\Omega\times\mathbf r+\mathbf v_{\rm def}\) reconstrueert ieder veld;
- `D2 mutual-linearity + all-on match`: directe mutual body-\(\Omega\) sluit met full-minus-isolated en het all-on masker sluit met de bestaande proxy;
- `D3 shapley-reconstruction`: vijf kanalen plus residual reconstrueren de counterfactualuitvoer;
- `D4 cyclic-index-invariance`: uniforme-arclengthresultaten zijn invariant onder cyclische node-indexshift;
- `D5 deterministic-repeat`: iedere bevroren analyse wordt direct een tweede keer uitgevoerd en moet dezelfde numerieke output opleveren.

`D5` controleert in deze versie de deterministische decompositie van dezelfde bevroren snapshot. De eerdere v7.6.15-benchmark blijft de afzonderlijke deterministische dynamica- en playbackcontrole.

## RESEARCH-uitvoer

- `R0 translation-leak`;
- `R1 parameterization-convergence` tussen \(N=128\) en \(N=192\);
- `R2 symmetry-parity` voor `ROT` en `MUTUAL_BS`;
- `R3 dominant-channel`, uitsluitend informatief;
- `R4 field-scale-comparison`, waarbij alleen `MUTUAL_BS` met de formele veldbracket wordt vergeleken.

Een research-FAIL verwerpt uitsluitend de onderzochte proxyconstructie of attributietak. Het is geen SST-falsificatie.

## UI en exports

Het paneel toont:

- voortgang over twintig snapshots;
- ENGINE- en RESEARCH-gates;
- A-, B- en nettobijdragen per kanaal;
- een kanaalbar/waterfallweergave;
- de laatste tien snapshotregels;
- een selector voor `ΔlnR phase`, `deltaFrac A−B` en `raw mutual Ω A−B`.

Beschikbare exports:

- TXT: volledig leesbaar auditrapport;
- JSON: schema `vortexlab-spec-clock-proxy-decomposition/1.0` met alle counterfactuals;
- CSV: één rij per snapshot en kanaal.

## Implementatiescope

De v7.6.16-runner gebruikt bewust de trefoil-botsingspreset. De exhaustive cyclic-shiftfit is daarmee getest voor één gesloten component per drager. De onderliggende snapshotstructuur bewaart componentmetadata, maar een aparte link/multicomponent-decompositieregressie valt buiten deze versie.

## Validatie

Uitgevoerd:

- inline JavaScript door `node --check`;
- HTML-audit: 412 unieke DOM-id’s, geen duplicaten;
- aanwezigheid van RUN-route, paneel, drie exports en solverhooks;
- pure regressietest voor vijfkanaals Shapley-identiteit;
- gewogen Kabsch-test: maximale synthetische posefout \(2.36\times10^{-8}\);
- rigid-fit-test: maximale fout \(6.94\times10^{-17}\);
- synthetische volledige counterfactualpipeline: all-on fout 0 en Shapley-residual \(1.08\times10^{-19}\).

Een volledige interactieve WebGL-run kon in de container niet betrouwbaar worden uitgevoerd: headless Chromium bleef in de permanente renderloop hangen. De daadwerkelijke twintig-snapshot-run moet daarom in de normale browser worden uitgevoerd en via TXT/JSON worden teruggekoppeld voor inhoudelijke beoordeling.
