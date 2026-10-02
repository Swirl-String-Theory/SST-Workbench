# VortexLab v7.6.18 — normalisatiebenchmark

Parent: `vortexring-lab-v7.6.17.html`  
Base: `v7.5.3`  
Proxy-decompositieschema: `vortexlab-spec-clock-proxy-decomposition/1.2`

## Vastgelegde conclusie van v7.6.17

De gewone SPEC CLOCK-benchmark en de proxy-decompositierunner sluiten beide technisch met `ENGINE=PASS`.

De v7.6.17-decompositie bevestigde:

- 21/21 pure en deterministische snapshots;
- een maximale absolute Shapley-reconstructierest van `2.0679515313825692e-25`;
- afzonderlijk geslaagde cyclic-indexcontroles voor het iso- en mutual-Ω-signaal;
- een vrijwel volledige ROT×MUTUAL-interactie:
  
  \[
  I_{R,M}=-1.6000886059741682\times10^{-9},
  \qquad
  \Delta\ln R_{\rm phase}=-1.6000278921144745\times10^{-9};
  \]

- een blijvende veldschaalmismatch van `3.5920685798601235e12` voor de Shapley-MUTUAL-attributie en `1.3595015263132936e10` voor de mutual-only counterfactual;
- nog geen volledige resolutieconvergentie: tussen `N=256` en `N=384` veranderen totaal, ROT, MUTUAL_BS en ROT×MUTUAL nog ongeveer `9.86%`;
- PARAM convergeert weg en TRANS is numeriek verwaarloosbaar.

Daarom is de huidige phase-nullproxy technisch reproduceerbaar, maar nog geen afgeleide SST-klokobservable. De volgende stap moet lokaliseren welk deel van de schaalmismatch door de gekozen dimensieloze noemer ontstaat.

## Nieuwe normalisatiebenchmark

De bestaande 21 passieve snapshots worden hergebruikt. Er komen geen extra solverstappen, feedbackkoppelingen of parameterfits bij.

Voor iedere drager worden de actuele en bij `t=0` gekalibreerde mutual body-frequenties langs zeven vooraf vastgelegde schalen geëvalueerd:

1. `ISO_DYNAMIC`
   
   \[
   q_i(t)=\frac{\Omega_{\mu,i}(t)}{|\Omega_{{\rm iso},i}(t)|}.
   \]

   Dit is de bestaande phase-nullnormalisatie en vormt een harde regressie-identiteit.

2. `ISO_REFERENCE`
   
   \[
   q_i(t)=\frac{\Omega_{\mu,i}(t)}{|\Omega_{{\rm iso},i}(0)|}.
   \]

3. `FULL_REFERENCE`
   
   \[
   q_i(t)=\frac{\Omega_{\mu,i}(t)}{|\Omega_{{\rm full},i}(0)|}.
   \]

4. `MUTUAL_REFERENCE`
   
   \[
   q_i(t)=\frac{\Omega_{\mu,i}(t)}{|\Omega_{\mu,i}(0)|}.
   \]

   Deze kandidaat wordt expliciet als kleine-noemer-/singulariteitsrisico gemarkeerd.

5. `CIRCULATION_LENGTH`
   
   \[
   D_{\Gamma L}=\frac{\Gamma_{\rm eff}}{L_0^2},
   \qquad q_i=\frac{\Omega_{\mu,i}}{D_{\Gamma L}}.
   \]

6. `RMS_ARCLENGTH`
   
   \[
   D_{uL}=\frac{u_{{\rm iso,rms},0}}{L_0},
   \qquad q_i=\frac{\Omega_{\mu,i}}{D_{uL}}.
   \]

7. `CORE_CIRCULATION`
   
   \[
   D_{\Gamma a}=\frac{\Gamma_{\rm eff}}{a_{\rm sim}^2},
   \qquad q_i=\frac{\Omega_{\mu,i}}{D_{\Gamma a}}.
   \]

Voor elke kandidaat worden geëxporteerd:

- actuele en calibratiewaarde per drager;
- gebruikte noemer per drager;
- lineaire offset `A−B`;
- `asinh`-getransformeerde offset;
- `log1p`-getransformeerde offset wanneer het domein geldig is;
- verhouding tot de formele veldbracket;
- A/B-traversalpariteit;
- resolutiereeks `N=128,192,256,384`;
- laatste relatieve verandering `N=256→384`.

## Nieuwe gates

### ENGINE D6 — normalization pipeline

Alle zeven schalen moeten op alle 21 snapshots eindig blijven. Bovendien moet:

\[
\Delta\ln R_{\rm ISO\_DYNAMIC}
=
\Delta\ln R_{\rm bestaande\ phase-null}
\]

binnen `1e-12` sluiten.

### RESEARCH R7 — normalization parity

Iedere schaal wordt getest op tekenomslag en magnitudemismatch onder de A/B-traversal-swap.

### RESEARCH R8 — normalization resolution convergence

Voor elke schaal wordt de laatste verandering tussen `N=256` en `N=384` bepaald:

- `≤5%`: PASS;
- `5–15%`: WARN;
- `>15%`: FAIL.

Een nuldoorgang blijft zichtbaar en wordt niet met een absolute waarde verborgen.

### RESEARCH R9 — field-scale ranking

De kandidaten worden gerangschikt op afstand tot de formele veldbracket. Dit is uitsluitend diagnostisch. Een nabijgelegen schaal is geen closure zonder een onafhankelijk afgeleide overdrachtswet.

### RESEARCH R10 — body-Ω denominator sensitivity

Vergelijkt `ISO_DYNAMIC`, `ISO_REFERENCE` en `FULL_REFERENCE` om vast te stellen hoeveel amplitude uitsluitend door de actuele versus bevroren body-Ω-noemer ontstaat.

## UI en export

De RUN-dropdown bevat nu ook:

`🧪 SST CLOCK · normalisatiebenchmark`

Deze optie start dezelfde passieve snapshotrunner en opent de normalisatieresultaten. De decompositie- en normalisatieresultaten worden samen geëxporteerd als TXT, JSON en CSV.

Nieuwe tabellen tonen:

- de zeven schalen, noemers, netto-uitkomst en veldschaalratio;
- de volledige resolutieladder per schaal.

## Wetenschappelijke grens

Geen kandidaatnormalisatie wordt door deze benchmark gecanoniseerd. De test voegt geen fitfactor toe en past geen SST-constante aan. De benchmark bepaalt uitsluitend waar de factor van ongeveer `10^8–10^12` in de huidige proxyconstructie ontstaat.
