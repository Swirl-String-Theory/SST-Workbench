# VortexLab v7.6.19 — transfer-law benchmark

**Versie:** 7.6.19  
**Parent:** 7.6.18  
**Basis:** 7.5.3  
**Schema proxy/decomposition:** `vortexlab-spec-clock-proxy-decomposition/1.3`

## Aanleiding

De gevalideerde v7.6.18-run sloot technisch volledig:

- gewone SPEC CLOCK-benchmark: `ENGINE PASS`;
- decompositie-, normalisatie- en convergentiepipeline: `ENGINE PASS`;
- researchproxy: `FAIL`;
- de keuze tussen actuele en bij `t=0` bevroren body-Ω-noemers veranderde de baseline slechts op relatieve schaal `≈3.2×10⁻⁹`;
- de beste niet-singuliere normalisatie, `Γ_eff/a_sim²`, bleef bij `N=128` circa `7.68×10⁸` en bij `N=384` circa `4.52×10⁸` boven de formele veldschaal;
- de niet-singuliere schalen veranderden tussen `N=256` en `N=384` nog ongeveer `9.8%`.

Daarmee is vastgelegd dat een andere denominator alleen de ontbrekende mapping niet levert. De volgende onderzoeksvraag is expliciet:

\[
\boxed{
\Delta\ln R
=
\mathcal T\!\left(
\Delta\Omega_{\rm mutual},
\Gamma,
a,
L,
d,
C_e,
r_c
\right)
}
\]

V7.6.19 implementeert deze vraag als een passieve, vooraf geregistreerde transfer-law benchmark.

## Wetenschappelijke grens

De benchmark:

- past geen solverstate aan;
- gebruikt dezelfde 21 bevroren snapshots als v7.6.17/v7.6.18;
- gebruikt nergens een achteraf gefitte gain;
- houdt voor iedere kandidaat de multiplicatieve coefficient exact gelijk aan `1`;
- rapporteert een eventuele vereiste coefficient uitsluitend diagnostisch en past die nooit toe;
- canoniseert geen kandidaat door alleen een numerieke schaalmatch.

## Vooraf geregistreerd transfer-lawregister

Alle kandidaten zijn dimensieloos. `ΔΩ` heeft dimensie `T⁻¹`, `Γ` heeft `L²T⁻¹`, `a,L,d,r_c` hebben `L` en `C_e` heeft `LT⁻¹`.

| ID | Kandidaatwet |
|---|---|
| `ADVECT_CORE` | `ΔΩ·a/C_e` |
| `ADVECT_LENGTH` | `ΔΩ·L/C_e` |
| `ADVECT_DISTANCE` | `ΔΩ·d/C_e` |
| `ADVECT_RC` | `ΔΩ·r_c/C_e` |
| `CIRC_CORE` | `ΔΩ·a²/Γ` |
| `CIRC_LENGTH` | `ΔΩ·L²/Γ` |
| `CIRC_DISTANCE` | `ΔΩ·d²/Γ` |
| `CIRC_CORE_D2` | `ΔΩ·a²/Γ·(a/d)²` |
| `CIRC_CORE_RC_D2` | `ΔΩ·a²/Γ·(r_c/d)²` |
| `ADVECT_LENGTH_A_D2` | `ΔΩ·L/C_e·(a/d)²` |
| `BUCKINGHAM_ALL` | `ΔΩ·Γ·a·L/(C_e²·d·r_c)` |

`BUCKINGHAM_ALL` is een expliciete Buckingham-monomiaal die alle zeven invoervariabelen gebruikt. Dit is een dimensie-diagnose, geen afgeleide fysische wet.

## Invoerconventie

Per drager wordt gebruikt:

\[
\Delta\Omega_i
=
\Omega_{i,\rm mutual}(t)
-
\Omega_{i,\rm mutual}(0).
\]

Daarna wordt iedere kandidaat afzonderlijk voor A en B geëvalueerd en wordt de netto-observable:

\[
\mathcal T_{AB}=\mathcal T_A-\mathcal T_B.
\]

De vaste invoeren zijn:

- `Γ`: arclength-gewogen effectieve circulatie van de referentiegeometrie;
- `a`: actieve simulatiekern `a_sim`;
- `L`: referentie-arclength `L₀` van de drager;
- `d`: actuele A–B-afstand van het snapshot;
- `C_e = 1.09384563×10⁶ m/s`;
- `r_c = 1.40897017×10⁻¹⁵ m`.

## Nieuwe ENGINE-gate

### D7 — transfer-law registry

D7 vereist tegelijkertijd:

1. alle monomialen sluiten op `L⁰T⁰`;
2. iedere coefficient is exact `1`;
3. alle wetten blijven eindig op alle 21 snapshots;
4. de directe netto-`ΔΩ_mutual` is identiek aan de bestaande raw-Ω-counterfactualroute.

De gate gebruikt een absolute raw-Ω-identiteitstolerantie van `1×10⁻¹⁸ s⁻¹`.

## Nieuwe RESEARCH-gates

### R11 — A/B-pariteit

Elke kandidaat moet onder de traversal-swap van teken veranderen en maximaal `10%` magnitudemismatch vertonen.

### R12 — static-null leakage

\[
\epsilon_{\rm null}
=
\frac{|\mathcal T_{\rm static-null}|}
{|\mathcal T_{\rm baseline}|}.
\]

- `≤1%`: PASS;
- `1–10%`: WARN;
- `>10%`: FAIL.

### R13 — resolutieconvergentie

De kandidaat wordt gevolgd bij `N=128,192,256,384`. Voor de laatste stap `N=256→384` geldt:

- `≤5%`: PASS;
- `5–15%`: WARN;
- `>15%`: FAIL.

Er wordt bij geen enkele resolutie opnieuw gefit.

### R14 — veldschaalrangschikking

Iedere kandidaat krijgt:

\[
\rho_{\rm field}
=
\frac{|\mathcal T_{AB}|}
{\max|\Delta\ln R_{\rm field}|}.
\]

Ook `requiredCoefficientToFieldEdge = 1/ρ_field` wordt geëxporteerd, maar nooit toegepast.

### R15 — no-fit admissibility

Een kandidaat wordt alleen als **KANDIDAAT** gemarkeerd wanneer tegelijk geldt:

- dimensieloos en coefficient `1`;
- `0.1 ≤ ρ_field ≤ 10`;
- pariteitsmismatch `≤10%`;
- static-nulllek `≤1%`;
- laatste resolutieverandering `≤5%`.

Een PASS van R15 is nog steeds geen afgeleide SST-klokwet; daarvoor blijft een onafhankelijke theoretische motivatie vereist.

## UI

De RUN-dropdown bevat nu:

`🧭 SST CLOCK · transfer-law benchmark`

Het bestaande decompositiepaneel bevat twee nieuwe tabellen:

1. formule, netto-uitkomst, veldratio, nuldriftlek, laatste resolutieverandering en besluit;
2. volledige `N=128–384`-reeks plus dimensie-identiteit per wet.

De gewone decompositie- en normalisatieruns berekenen dezelfde transfer-lawgegevens automatisch, zodat de drie diagnoses exact dezelfde snapshots gebruiken.

## Export

TXT en JSON bevatten nu:

- `transferLawDefinitions`;
- per snapshot de volledige A/B-inputs;
- per wet A, B, netto-uitkomst en veldratio;
- de dimensie-exponenten;
- de vaste coefficient;
- de niet-toegepaste `requiredCoefficientToFieldEdge`;
- D7 en R11–R15.

CSV voegt records met `recordType=TRANSFER_LAW` toe.

## Preflight op de echte v7.6.18-export

De nieuwe wetten zijn offline doorgerekend op de eerder geëxporteerde 21 snapshots. Dit is een preflight, nog geen v7.6.19-browserrun.

Voor de baseline bij `N=128`, `t=3 s`:

| Wet | Netto | Veldratio |
|---|---:|---:|
| `ADVECT_LENGTH` | `−1.0871×10⁻²¹` | `4.888` |
| `ADVECT_DISTANCE` | `−1.2254×10⁻²¹` | `5.511` |
| `BUCKINGHAM_ALL` | `−8.4323×10⁻²⁴` | `3.792×10⁻²` |
| `ADVECT_CORE` | `−1.5129×10⁻²⁴` | `6.803×10⁻³` |
| `CIRC_CORE` | `−1.7089×10⁻¹³` | `7.685×10⁸` |

`ADVECT_LENGTH` en `ADVECT_DISTANCE` liggen zonder fitfactor binnen één decade van de formele veldschaal. Zij worden in de preflight desondanks afgewezen, omdat hun laatste resolutiestap nog respectievelijk ongeveer `9.83%` en `9.84%` verandert. Alle kandidaten hebben een static-nulllek van slechts ongeveer `3.5–4.1×10⁻⁵` en correcte A/B-pariteit, maar geen kandidaat haalt alle R15-voorwaarden tegelijk.

## Niet gewijzigd

- geen wijziging aan Biot–Savart, LIA, RK4 of CFL;
- geen wijziging aan topology guard of contactgrenzen;
- geen wijziging aan SST/CANON-constanten;
- geen wijziging aan de tien-run SPEC CLOCK-benchmark;
- geen vrije gain of parameterfit;
- geen solverfeedback vanuit de transfer-lawbenchmark.

## Validatie

- inline JavaScript: syntaxcontrole geslaagd;
- DOM: `419` unieke id’s, geen duplicaten;
- transfer-lawregister: `11/11` dimensieloos;
- transfer-lawcoëfficiënten: `11/11` exact `1`;
- geïsoleerde JavaScript-test van het nieuwe register geslaagd;
- replay op de 21 v7.6.18-snapshots: maximale raw-`ΔΩ`-identiteitsfout `1.84×10⁻²⁸ s⁻¹`;
- bestaand decompositie- en normalisatieschema behouden en verhoogd naar schema `1.3`.

Een volledige WebGL-browserrun kon in de container niet worden uitgevoerd omdat lokale HTTP- en `file://`-navigatie door het beheerde Chromiumbeleid wordt geblokkeerd. De echte v7.6.19-export blijft daarom de definitieve runtimecontrole.
