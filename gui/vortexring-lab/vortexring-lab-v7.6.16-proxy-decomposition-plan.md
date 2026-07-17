# VortexLab v7.6.16 — implementatieplan proxy-decompositiebenchmark

**Status:** ontwerp en acceptatieplan; nog niet geïmplementeerd  
**Parent:** VortexLab v7.6.15  
**Modelstatus:** Research Track, strikt passief en niet-canoniek

## 1. Doel

De benchmark moet verklaren waardoor de gemeten

\[
\Delta\ln R_{AB}^{\rm phase-null}
\]

wordt opgebouwd. Per drager A en B, per vast meettijdstip, worden vijf gevraagde bijdragen onderscheiden:

1. geometrische vervorming;
2. parametrisatie/arclength-redistributie;
3. rigid-body-rotatie;
4. translatie en translatielekkage;
5. directe wederzijdse Biot–Savart-bijdrage.

Daarnaast wordt altijd een zesde kanaal gerapporteerd:

6. niet-lineaire koppeling/reconstructieresidual.

De benchmark mag geen nieuwe fysische sluiting aannemen. Hij bepaalt uitsluitend welke numerieke en kinematische mechanismen de bestaande proxy produceren.

## 2. Waarom een naïeve aftrek niet volstaat

De proxy bevat delingen door \(|\Omega_i^{\rm iso}|\), een verre referentieaftrek en `log1p`. Daardoor is zij niet lineair in geometrie en snelheid. Een reeks verschillen zoals “eerst translatie aftrekken, daarna rotatie” is volgorde-afhankelijk.

De implementatie gebruikt daarom twee lagen:

- een lineaire, arclength-gewogen kinematische decompositie van de puntsnelheden;
- een counterfactual/Shapley-attributie van de uiteindelijke niet-lineaire \(\Delta\ln R\)-uitvoer.

De som van alle attributies plus de residual moet de werkelijk gemeten proxy reconstrueren.

## 3. Bevroren snapshots

De dynamische run blijft de bestaande v7.6.15 solver gebruiken. Op vooraf vastgelegde checkpoints wordt een read-only snapshot gemaakt van:

- `Y` en de filamentmetadata;
- volledige snelheid \(\mathbf V^{\rm full}\);
- geïsoleerde snelheden \(\mathbf V_A^{\rm iso}\) en \(\mathbf V_B^{\rm iso}\);
- het directe bronveld \(\mathbf V_{A\leftarrow B}^{\rm mutual}\) en \(\mathbf V_{B\leftarrow A}^{\rm mutual}\);
- cumulatieve arclength en segmentgewichten;
- calibratiegeometrie en calibratieproxy;
- centra, pose en topologische diagnostiek.

Geen counterfactual mag `Y`, `K4`, `tPhys`, `stepDebt`, de topology guard of de fase-nullreferentie wijzigen.

Aanbevolen checkpoints voor de eerste benchmark:

\[
t=0,\ 0.5,\ 1.0,\ 2.0,\ 3.0\ \mathrm{s}.
\]

De laatste geaccepteerde stap landt exact op ieder checkpoint.

## 4. Canonieke curve-representatie per snapshot

Voor iedere drager wordt een periodieke curve \(\mathbf q_i(s)\), \(s\in[0,1)\), opgebouwd met arclength-gewogen periodieke interpolatie.

Er worden twee samplegrids bijgehouden:

- **live grid:** de actuele knooppuntsparametrisatie;
- **uniform grid:** exact uniforme genormaliseerde arclength.

De actuele curve wordt met een gewogen Kabsch/Procrustes-fit aan de calibratiecurve ontbonden als

\[
\mathbf x_i(s,t)=
\mathbf c_i(t)+
\mathbf Q_i(t)\big[\mathbf q_{i,0}(s)+\mathbf d_i(s,t)\big],
\]

waar:

- \(\mathbf c_i\): translatie/centrumpositie;
- \(\mathbf Q_i\in SO(3)\): rigid pose;
- \(\mathbf d_i\): intrinsieke geometrische vervorming na poseverwijdering.

De fit gebruikt arclengthgewichten en legt de periodieke indexshift vast door de minimale RMS-afstand te kiezen. Hierdoor wordt een cyclic node shift niet onterecht als vormverandering gemeten.

## 5. Arclength-gewogen rigid-motion-fit van de snelheid

Voor ieder snelheidsveld wordt de gewogen least-squares-fit berekend:

\[
\mathbf v_j=
\mathbf U+
\boldsymbol\Omega_{\rm rigid}\times
(\mathbf x_j-\mathbf c)
+
\mathbf v_{{\rm def},j}.
\]

Uitvoer:

- \(\mathbf U\): centroidtranslatie;
- \(\boldsymbol\Omega_{\rm rigid}\): volledige 3D rigid-body-hoeksnelheid;
- \(\mathbf v_{\rm def}\): niet-rigide residual;
- relatieve reconstructiefout in de gewogen \(L^2\)-norm.

Dit vervangt de huidige diagnostiek niet. Het is een afzonderlijke benchmarkfit waarmee zichtbaar wordt hoeveel de bestaande z-body-\(\Omega\)-functionaal projecteert uit elk snelheidskanaal.

## 6. De vijf attributiekanalen

### 6.1 Geometrische vervorming — `GEOM`

Doel: meten hoeveel de actuele intrinsieke vorm \(\mathbf d_i(s,t)\) de body-\(\Omega\)-projectie en de niet-lineaire faseproxy moduleert.

Counterfactual:

- behoud actuele snelheid als functie van canonieke arclength;
- vervang de actuele posevrije curve door de calibratiecurve;
- behoud dezelfde uniforme sampling en dezelfde rigid pose;
- transporteer de snelheid via dezelfde lokale arclengthcorrespondentie.

Het verschil tussen actuele en vormbevroren proxy is de vormgevoeligheid. De Kabsch-pose zelf behoort niet tot dit kanaal.

### 6.2 Parametrisatie/arclength-redistributie — `PARAM`

Doel: vaststellen hoeveel de discrete nodeverdeling de body-\(\Omega\)-meting beïnvloedt zonder de geometrische curve te veranderen.

Counterfactual:

- evalueer exact dezelfde geïnterpoleerde curve en snelheid eenmaal op het live grid en eenmaal op een uniform-arclengthgrid;
- gebruik in beide gevallen segmentgewogen integralen;
- rapporteer tevens segmentratio \(\ell_{\max}/\ell_{\min}\).

Het verschil is parametrisatielekkage. In de continuumlimiet hoort dit kanaal naar nul te convergeren.

### 6.3 Rigid-body-rotatie — `ROT`

Doel: meten welk deel van de proxy afkomstig is van de best-fit rigid rotation.

Counterfactual:

\[
\mathbf V_{\rm no\,rot}
=
\mathbf V-\boldsymbol\Omega_{\rm rigid}\times\mathbf r.
\]

De translatie blijft bij deze ablation behouden. Zowel de volledige als de geïsoleerde route wordt opnieuw geëvalueerd, zodat geen inconsistent verschilveld ontstaat.

Rapporteer:

- \(\boldsymbol\Omega_{\rm rigid}^{\rm full}\);
- \(\boldsymbol\Omega_{\rm rigid}^{\rm iso}\);
- het mutual verschil;
- projectie op de bestaande z-body-\(\Omega\)-diagnostiek.

### 6.4 Translatie en translatielekkage — `TRANS`

Doel: controleren of uniforme centroidbeweging in de discrete body-\(\Omega\)-functionaal lekt.

Counterfactual:

\[
\mathbf V_{\rm no\,trans}=\mathbf V-\mathbf U.
\]

In het continue, exact gecentreerde geval hoort uniforme translatie nul bijdrage te leveren. Daarom krijgt dit kanaal twee uitlezingen:

- fysieke centroidtranslatie \(|\mathbf U|\);
- numerieke translatielekkage in \(\Delta\ln R_{AB}^{\rm phase-null}\).

Een grote centroidtranslatie is niet automatisch een fout; alleen een grote lekkage in de rotatieproxy is problematisch.

### 6.5 Direct wederzijds Biot–Savart — `MUTUAL_BS`

Doel: het werkelijk door de andere drager geïnduceerde snelheidsveld isoleren.

Bereken rechtstreeks:

\[
\mathbf V_{A\leftarrow B}^{\rm mutual},
\qquad
\mathbf V_{B\leftarrow A}^{\rm mutual}
\]

met dezelfde segmentkernel, \(a_{\rm sim}\), broncirculaties en snapshotgeometrie als de solver, maar zonder zelfveld of achtergrondveld.

ENGINE-identiteit:

\[
\Omega_i[\mathbf V^{\rm full}]
-
\Omega_i[\mathbf V^{\rm iso}]
\stackrel{?}{=}
\Omega_i[\mathbf V_i^{\rm mutual}].
\]

Omdat de body-\(\Omega\)-functionaal lineair in \(\mathbf V\) is, moet deze identiteit tot floating-pointtolerantie sluiten. Daarna wordt gemeten hoeveel van de uiteindelijke niet-lineaire faseproxy door dit directe mutual kanaal wordt verklaard.

## 7. Shapley/counterfactual-attributie

Definieer vijf toggles:

\[
S=\{G,P,R,T,M\}.
\]

Voor ieder subset \(A\subseteq S\) wordt de faseproxy \(F(A)\) op hetzelfde snapshot geëvalueerd. Een toggle “aan” gebruikt de actuele toestand; “uit” gebruikt de vooraf vastgelegde referentie/ablation.

Voor kanaal \(k\) is de Shapley-bijdrage:

\[
\phi_k=
\sum_{A\subseteq S\setminus\{k\}}
\frac{|A|!(5-|A|-1)!}{5!}
\left[F(A\cup\{k\})-F(A)\right].
\]

Met vijf kanalen zijn per checkpoint 32 counterfactuals nodig. Dat is acceptabel omdat dit alleen op bevroren benchmarkcheckpoints gebeurt.

Reconstructie:

\[
F(S)-F(\varnothing)
=
\phi_G+\phi_P+\phi_R+\phi_T+\phi_M
+\varepsilon_{\rm recon}.
\]

`epsilon_recon` moet uitsluitend floating-point- en interpolatiefout bevatten. De benchmark rapporteert zowel absolute als relatieve residual.

## 8. Benchmarkscenario's

De eerste v7.6.16-run gebruikt vier dynamische scenario's:

1. **baseline:** \(v_{z,A}=+5\) mm/s, \(v_{z,B}=-5\) mm/s;
2. **static-null:** beide opgelegde drifts nul;
3. **A/B traversal swap:** circulatierichtingen omgewisseld;
4. **resolution pair:** dezelfde baseline op standaardresolutie en één hogere vaste resolutie.

De decompositie vindt binnen ieder scenario plaats op dezelfde checkpoints. Cilinder- en playbacktests hoeven niet opnieuw in deze runner te worden opgenomen; die zijn al door v7.6.15 als ENGINE-invarianties gevestigd, maar blijven in de bestaande benchmark beschikbaar.

## 9. Gates

### ENGINE-gates

- `D0 snapshot-purity`: hash/checksum van `Y`, `tPhys` en calibratiestatus vóór en na iedere snapshotanalyse is identiek.
- `D1 velocity-reconstruction`: \(\mathbf U+\Omega\times r+v_{\rm def}\) reconstrueert het invoerveld binnen vaste relatieve tolerantie.
- `D2 mutual-linearity`: direct mutual body-\(\Omega\) sluit met full-minus-isolated.
- `D3 shapley-reconstruction`: som van attributies plus baseline reconstrueert de actuele faseproxy.
- `D4 cyclic-index-invariance`: een cyclische node-indexshift verandert de uniforme-arclengthuitkomst niet.
- `D5 deterministic-repeat`: twee identieke decompositieruns leveren dezelfde JSON-uitvoer, afgezien van timestamps.

### RESEARCH-gates/rapporten

- `R0 translation-leak`: rapporteert translatielekkage; alleen een ruime engineeringgrens bepaalt PASS/WARN.
- `R1 parameterization-convergence`: `PARAM` moet afnemen bij hogere resolutie/uniforme sampling.
- `R2 symmetry-parity`: onder A/B-swap keren de ondertekende mutual- en rotatieattributies volgens de gemeten proxypariteit om.
- `R3 dominant-channel`: informatief rangschikken van \(|\phi_k|\); geen vooraf opgelegde winnaar.
- `R4 field-scale-comparison`: vergelijk uitsluitend `MUTUAL_BS` met de formele veldbracket; geometrie-, PARAM-, ROT- en TRANS-kanalen mogen niet als veldclosure worden geïnterpreteerd.

Geen researchgate mag SST of een klokwet falsificeren. Zij beoordeelt alleen de huidige proxyconstructie.

## 10. UI

Toevoegen aan de RUN-dropdown:

> 🧬 SST CLOCK · proxy-decompositiebenchmark

Nieuw benchmarkpaneel:

- start/stop;
- checkpointvoortgang;
- per kanaal een ondertekende waarde en percentage van \(|\Delta\ln R|\);
- afzonderlijke A- en B-tabellen;
- stacked waterfall voor de vijf Shapley-bijdragen plus residual;
- toggle tussen `raw Ω`, `deltaFrac` en `ΔlnR`;
- TXT/JSON/CSV-export.

De UI moet steeds tonen:

> PASSIEVE DECOMPOSITIE · geen solverfeedback · geen canonieke fase-observable.

## 11. Exportschema

Voorgesteld schema:

`vortexlab-spec-clock-proxy-decomposition/1.0`

Minimaal per snapshot:

- scenario-id en checkpointtijd;
- geometriehash en parametergridhash;
- centra, Kabsch-rotatie en fit-RMS;
- \(\mathbf U\), \(\boldsymbol\Omega_{\rm rigid}\), residualnorm;
- full/iso/mutual body-\(\Omega\);
- alle 32 counterfactualwaarden;
- Shapley-bijdragen `GEOM`, `PARAM`, `ROT`, `TRANS`, `MUTUAL_BS`;
- reconstructieresidual;
- formele veldbracket;
- topology gap en relevante numerieke metadata.

## 12. Prestatiegrenzen

De runner analyseert uitsluitend checkpoints en niet iedere geaccepteerde stap. De 32 counterfactuals gebruiken vooraf berekende/interpoleerde snapshotvelden waar mathematisch toegestaan. De directe Biot–Savart-mutualvelden worden eenmaal per checkpoint berekend en gecachet.

De benchmark mag het dynamische traject niet aanpassen om sneller te worden. UI-rendering kan worden verlaagd, maar de geaccepteerde solverstappen blijven identiek.

## 13. Acceptatiecriteria voor v7.6.16

De versie is gereed wanneer:

1. alle ENGINE-gates D0–D5 slagen;
2. dezelfde benchmark tweemaal deterministisch reproduceert;
3. de vijf attributies en residual voor ieder checkpoint worden geëxporteerd;
4. `MUTUAL_BS` onafhankelijk via direct veld en full-minus-isolated sluit;
5. de analyse aantoonbaar geen solverstate wijzigt;
6. de changelog duidelijk vermeldt dat dominantie van een kanaal nog geen SST-klokwet afleidt;
7. er geen fitfactor wordt toegevoegd om de bestaande closure-fout kunstmatig te verkleinen.

## 14. Beslismoment na de benchmark

- **MUTUAL_BS domineert en residual is klein:** de body-Ω-proxy meet werkelijk mutual rotatie, maar de overdracht van mutual snelheid/rotatie naar klokrate is verkeerd of ontbreekt. Volgende stap: een afgeleide fase-observable/transfer law, niet verdere numerieke tuning.
- **GEOM of ROT domineert:** de proxy meet vooral kinematische vorm- of poseverandering en is ongeschikt als lokale klokobservable.
- **PARAM domineert of convergeert niet:** de proxy is discretisatieafhankelijk en moet worden vervangen door een reparametrisatie-invariante functionaal.
- **TRANS is materieel:** er bestaat een centrerings/weging-lek in de body-Ω-projectie; eerst ENGINE-fix uitvoeren.
- **Residual is groot:** de gekozen counterfactualfactorisatie is onvoldoende; geen wetenschappelijke interpretatie totdat reconstructie sluit.
