# VortexLab v7.6.17 — benchmarkupgrade

Parent: **v7.6.16**  
Base: **v7.5.3**  
Proxy-decompositieschema: **vortexlab-spec-clock-proxy-decomposition/1.1**

## Vastgelegde conclusie van de v7.6.16-run

De eerste echte browserrun van de proxy-decompositie voltooide alle 20 geplande snapshots. Snapshot-purity, snelheidsreconstructie, mutual-linearity, all-on-proxymatch en deterministische herhaling slaagden.

De gemelde `ENGINE FAIL D3` was geen mislukte Shapley-decompositie. Bij de nulcheckpoints waren zowel de totale counterfactual-uitkomst als de absolute reconstructierest praktisch nul. De oude gate deelde de rest vervolgens door een kunstmatige noemer van `1e-300`, waardoor een betekenisloze relatieve fout van orde `1e263` ontstond. De grootste absolute Shapley-rest in de volledige run was slechts:

\[
2.07\times10^{-25}.
\]

Wanneer dezelfde export met de v7.6.17-gemengde tolerantie wordt beoordeeld, is de grootste residualscore ongeveer:

\[
2.15\times10^{-6}<1,
\]

zodat D3 terecht **PASS** wordt.

De wetenschappelijke uitkomst blijft negatief voor de huidige faseproxy. Op het baselinecheckpoint bij \(t=3\,\mathrm{s}\) was:

\[
\Delta\ln R_{AB}^{\rm phase}=-1.6000278921\times10^{-9}.
\]

De Shapley-verdeling was ongeveer:

- `ROT`: \(-8.0003207\times10^{-10}\);
- `MUTUAL_BS`: \(-7.9879787\times10^{-10}\);
- `PARAM`: \(-1.8554607\times10^{-12}\);
- `GEOM`: \(+6.5750872\times10^{-13}\);
- `TRANS`: verwaarloosbaar.

Deze ongeveer 50/50-verdeling is geen bewijs voor twee onafhankelijke fysieke helften. De expliciete tweekanaalsinteractie was:

\[
I_{R,M}=v(R+M)-v(R)-v(M)+v(0)
       =-1.6000886\times10^{-9},
\]

vrijwel de volledige proxy. De proxy meet dus hoofdzakelijk een niet-lineaire **ROT×MUTUAL-normalisatie-interactie**.

De amplitude was bovendien niet resolutiegeconvergeerd. Tussen \(N=128\) en \(N=192\) daalde de totale proxy circa 25.5%. De formele closure bleef ook na verwijdering van de gedeelde Shapley-interactie negatief: de mutual-only counterfactual lag nog ongeveer \(1.36\times10^{10}\) boven de formele veldbracket.

## Wijzigingen in v7.6.17

### D3 — zero-safe Shapley-reconstructie

De oude zuiver relatieve fout is vervangen door:

\[
|\varepsilon_{\rm recon}|\le
\varepsilon_{\rm abs}
+\varepsilon_{\rm rel}
\max\!\left(
|v(31)-v(0)|,
\sum_i|\phi_i|,
|v_{\rm full}-v_{\rm baseline}|
\right).
\]

Toleranties:

- `phaseLog`: \(\varepsilon_{\rm abs}=10^{-24}\);
- `deltaFrac`: \(\varepsilon_{\rm abs}=10^{-24}\);
- `rawOmega`: \(\varepsilon_{\rm abs}=10^{-30}\);
- alle kanalen: \(\varepsilon_{\rm rel}=10^{-10}\).

De export rapporteert voortaan absolute rest, schaal, tolerantie en mixed residualscore.

### D4 — cyclische-indexinvariantie op twee schalen

De benchmark rapporteert afzonderlijk:

- relatieve fout van het grote geïsoleerde body-\(\Omega\)-veld;
- relatieve fout van de veel kleinere mutual-\(\Omega\)-increment.

PASS-grenzen:

\[
\varepsilon_{\rm cyc}^{\rm iso}\le10^{-5},
\qquad
\varepsilon_{\rm cyc}^{\rm mutual}\le0.1.
\]

Hierdoor kan een kleine fout tegenover de zelfrotatie niet meer een grote fout tegenover het mutual-signaal verbergen.

### Resolutieladder

De scenario’s zijn uitgebreid naar:

- baseline \(N=128\), checkpoints \(0,0.5,1,2,3\,\mathrm{s}\);
- nuldrift \(N=128\), dezelfde checkpoints;
- A/B-traversal-swap \(N=128\), dezelfde checkpoints;
- \(N=192\), checkpoints \(0,3\,\mathrm{s}\);
- \(N=256\), checkpoints \(0,3\,\mathrm{s}\);
- \(N=384\), checkpoints \(0,3\,\mathrm{s}\).

Totaal: **21 passieve snapshots**.

De nieuwe gate `R6 resolution-ladder convergence` volgt:

- totale \(\Delta\ln R\);
- `ROT`;
- `MUTUAL_BS`;
- \(I_{R,M}\).

De laatste stap \(N=256\rightarrow384\) bepaalt het verdict:

- PASS: maximaal 5% verandering;
- WARN: maximaal 15%;
- FAIL: meer dan 15%.

### Expliciete ROT×MUTUAL-export

Voor `phaseLog`, `deltaFrac` en `rawOmega`, zowel netto als afzonderlijk voor A en B, worden nu opgeslagen:

\[
v(0),\quad v(R),\quad v(M),\quad v(R+M),\quad
I_{R,M},\quad v(\mathrm{all\ on}).
\]

De UI bevat een interactietabel en een resolutietabel. TXT, JSON en CSV bevatten dezelfde gegevens.

### Veldschaalgate

De veldvergelijking rapporteert nu twee verschillende grootheden:

1. de Shapley-attributie `MUTUAL_BS`, waarin een deel van de ROT×MUTUAL-interactie kan zitten;
2. de directe mutual-only counterfactual \(v(M)-v(0)\).

Beide moeten binnen de formele veldbracket vallen om de gate te laten slagen.

## Wetenschappelijke grens

De benchmark blijft strikt passief. Geen gate, Shapley-attributie of interactieterm wordt teruggekoppeld naar de solver. Een dominante, convergente of symmetrische proxycomponent vormt nog geen afgeleide SST-klokobservable of overdrachtswet.

De v7.6.16-run rechtvaardigt daarom:

- **ENGINE-algoritmiek:** numeriek consistent na correctie van D3;
- **huidige phase-nullproxy:** niet gevalideerd;
- **SST/CANON:** niet gefalsificeerd door deze proxytest.
