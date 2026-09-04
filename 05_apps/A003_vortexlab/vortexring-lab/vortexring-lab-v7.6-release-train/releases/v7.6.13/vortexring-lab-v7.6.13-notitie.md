# VortexLab v7.6.13 — automatische SPEC CLOCK-benchmark

## Doel

v7.6.13 voegt één reproduceerbare benchmarkworkflow toe voor de niet-canonieke twee-knoop SPEC CLOCK-diagnostiek. De gebruiker hoeft niet langer handmatig dezelfde configuratie te resetten, opnieuw te kalibreren, verschillende afspeelsnelheden te kiezen, cilinderhoogtes te wisselen en BEM-/oriëntatievarianten naast elkaar te leggen.

De benchmark verandert de SST-canon niet. Zij test enerzijds de implementatie-integriteit van de simulator en anderzijds afzonderlijk de research-track fase-nullproxy.

## Starten

Gebruik één van deze twee routes:

1. Kies in de header-dropdown **🧪 SST CLOCK · automatische benchmark**.
2. Of open het SPECULATIVE SWIRL CLOCK-paneel en klik **▶ Run volledige benchmark**.

De benchmark vervangt de lopende simulatie door schone onafhankelijke runs. Na voltooiing worden de vooraf ingestelde modelparameters teruggezet en wordt de configuratie opnieuw opgebouwd bij `t = 0`.

## Automatische volgorde: tien runs

1. **Baseline** — SST, trefoil, botsing, Biot–Savart, hoog, `a_sim = 1 mm`, totale cilinderhoogte `1.0 m`, drift `±5 mm/s`, BEM-keuze aan maar bundel uit, playback `16×`, doeltijd `3 s`.
2. **Nuldrift** — dezelfde configuratie met `v_z,A = v_z,B = 0`, doeltijd `4 s`.
3. **Playback 1×** — baselinefysica, doeltijd `2 s`.
4. **Playback 4×** — baselinefysica, doeltijd `2 s`.
5. **Playback 16×** — baselinefysica, doeltijd `2 s`.
6. **Extra hoge cilinder** — totale hoogte `5.0 m`, overige baseline-instellingen, doeltijd `3 s`.
7. **Drift ±1.0 mm/s** — doeltijd `3 s`.
8. **Drift ±2.5 mm/s** — doeltijd `3 s`.
9. **A/B traversal omgewisseld** — `ccwA=false`, `ccwB=true`, doeltijd `3 s`.
10. **BEM uit** — bundel blijft uit, BEM-keuze uit, doeltijd `3 s`.

Iedere run voert automatisch deze cyclus uit:

`preset → vaste scenario-instellingen → volledige reset → fase-nullkalibratie bij t=0 → start → exacte landing op doeltijd → resultaatopname`.

## Exacte doeltijdlanding

De benchmark begrenst de eerstvolgende geaccepteerde CFL-stap met de resterende tijd tot het scenario-einde:

\[
\Delta t_{\rm bench}
=
\min\!\left(\Delta t_{\rm CFL},\,t_{\rm target}-t_{\rm phys}\right).
\]

Hierdoor worden 1×, 4× en 16× bij exact dezelfde fysische tijd vergeleken. Framerate-overshoot kan de vergelijking niet vervuilen.

## Twee gescheiden verdicts

### ENGINE

Deze gates beoordelen de code en reproduceerbaarheid:

- kalibratie bij `t=0`, geldige sample en eerste stap `dt₁ ≤ 0.05 s` voor alle runs;
- invariatie tussen playback `1×`, `4×` en `16×`;
- invariatie tussen totale cilinderhoogte `1 m` en `5 m` wanneer `bgFlow=none` en de bundel uitstaat;
- BEM-negatieve controle wanneer de bundel uitstaat.

Een ENGINE FAIL wijst op een implementatie-, state- of integratorprobleem.

### RESEARCH PROXY

Deze gates beoordelen uitsluitend de huidige niet-afgeleide fase-nullproxy:

- nuldrift-fasestabiliteit;
- teken- en magnitudesymmetrie na omwisseling van A/B traversal;
- trend van afstand en fasegrootte bij de driftsweep;
- ligging van de fase-nullratio binnen de formele veldbracket.

Een RESEARCH PROXY FAIL verwerpt alleen deze proxyrealisatie. Het is geen falsificatie van SST, canonieke parameters of een nog niet afgeleide klokwet.

## Rapportage

Het paneel toont per run:

- fysische eindtijd;
- actuele A–B-afstand;
- `Δln R_phase-null`;
- grootste absolute veldbracketwaarde;
- geïntegreerde fase-lag;
- eerste geaccepteerde tijdstap.

Na afloop kunnen twee rapporten worden gedownload:

- `vortexlab-spec-clock-benchmark-7-6-13.txt`
- `vortexlab-spec-clock-benchmark-7-6-13.json`

ModelLog registreert daarnaast:

- benchmarkstart;
- scenario-instellingen;
- afzonderlijke scenarioresultaten;
- eindverdicts;
- `Rcyl`, `Hcyl` en totale cilinderhoogte in iedere parametersnapshot.

## Aanvullende correctie

Een handmatige wijziging van diameter of hoogte terwijl SPEC CLOCK actief is:

- maakt de bestaande fase-nullkalibratie ongeldig;
- pauzeert de run;
- wist het playback-debet;
- vereist een nieuwe kalibratie.

Dit voorkomt dat een referentie uit een andere volume-/achtergrondgeometrie stilzwijgend wordt hergebruikt.

## Versiestatus

Deze wijziging is v7.6.13 en geen nieuw fysisch model:

- filament-ODE, Biot–Savart/LIA-kernels en SST-parameters zijn niet gewijzigd;
- de benchmark is een orchestratie-, logging- en validatielaag;
- de fase-null- en stabiele veldformules uit v7.6.11/v7.6.12 blijven inhoudelijk gelijk.
