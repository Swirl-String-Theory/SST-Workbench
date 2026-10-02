# VortexLab v7.6.21 — canonieke `L/v↺*` lengte-identificatiebenchmark

Parent: **v7.6.20**  
Base: **v7.5.3**  
Schema: `vortexlab-spec-clock-proxy-decomposition/1.5`

## Doel

V7.6.21 splitst de eerdere generieke advectieve transferterm

\[
\Delta\Omega_{\rm mutual}\frac{L}{v_{\!\boldsymbol{\circlearrowleft}}^{\ast}}
\]

op in expliciete fysische en negatieve-controlelengtes. De benchmark beantwoordt twee verschillende vragen:

1. **Welke geometrische grootheid is volgens CANON bedoeld met `L_K`?**
2. **Sluit die lengte numeriek met de formele veldroute zonder vrije fitcoëfficiënt?**

## Canon-audit

De actuele CANON definieert voor een gesloten vortexfilament:

\[
\tau_{\rm circ}(K)=\frac{L_K}{v_{\!\boldsymbol{\circlearrowleft}}^{\ast}},
\]

waar `L_K` de effectieve/opgeloste gesloten centerline-lengte van de drager is.

Alleen voor de minimale neutrale lus geldt de speciale reductie

\[
L_K=2\pi r_c,
\qquad
\tau_{\rm circ,c}=\frac{2\pi r_c}{v_{\!\boldsymbol{\circlearrowleft}}^{\ast}}
=\frac{2\pi}{\omega_c}.
\]

Voor een ideale finite-thickness tube geldt in diameterconventie:

\[
L_K=\operatorname{Rop}_{\rm diam}(K)\,D_K
=2a_{\rm core}\operatorname{Rop}_{\rm diam}(K).
\]

Voor de trefoil gebruikt het project:

\[
\operatorname{Rop}_{\rm diam}(3_1)=16.371637,
\qquad
\operatorname{Rop}_{\rm rad}(3_1)=32.743274.
\]

De opgeloste tube-radius is geometrisch:

\[
a_{\rm core}
=\operatorname{reach}(\gamma_K)
=\min\!\left(\inf_s\frac1{\kappa(s)},\frac12d_{\rm dcsd}\right),
\]

en mag niet ongemotiveerd gelijk worden gesteld aan `r_c` of `a_sim`.

## Tien lengteklassen

1. `RESOLVED_CURRENT` — actuele centerline-integraal `L_K(t)`; canonieke geometrische klasse.
2. `RESOLVED_REFERENCE` — centerline-lengte van de kalibratietoestand `L_K(0)`; canonieke geometrische klasse.
3. `IDEAL_REACH_CURRENT` — `16.371637 × 2a_core(t)`, met `a_core` benaderd door reach/thickness.
4. `IDEAL_REACH_REFERENCE` — dezelfde ideal-tube mapping met de kalibratie-thickness.
5. `IDEAL_ASIM_DIAMETER` — `16.371637 × 2a_sim`; **numerieke negatieve controle**.
6. `TREFOIL_RC_DIAMETER_BENCHMARK` — `16.371637 × 2r_c`; expliciete Research-Track schaalbenchmark, geen bewijs voor `a_core=r_c`.
7. `MINIMAL_NEUTRAL_LOOP` — `2πr_c`; alleen de canonieke speciale neutrale lus.
8. `COMPTON_WAVELENGTH` — `λ_c=2πc/ω_c`; referentieschaal.
9. `REDUCED_COMPTON` — `λ̄_c=c/ω_c`; referentieschaal.
10. `DISTANCE_CONTROL` — `d_AB`; negatieve controle omdat dit geen gesloten carrierlengte is.

## Twee strikt gescheiden routes

### Absolute route

\[
Q_L^{\rm abs}(t)
=
\frac{
\Omega_{\rm mutual,A}(t)L_A(t)
-
\Omega_{\rm mutual,B}(t)L_B(t)
}{v_{\!\boldsymbol{\circlearrowleft}}^{\ast}}.
\]

Deze route wordt uitsluitend vergeleken met de absolute formele veldbracket op hetzelfde checkpoint.

### Gekalibreerde route

\[
\delta Q_L(t)
=
Q_L^{\rm abs}(t)-Q_L^{\rm abs}(0).
\]

Deze route wordt uitsluitend vergeleken met

\[
\delta\ln R_{\rm field}(t)
=
\Delta\ln R_{\rm field}(t)
-
\Delta\ln R_{\rm field}(0).
\]

Hiermee is de v7.6.19-vergelijkingsfout — gekalibreerde `ΔΩ` tegenover een absolute veldwaarde — verwijderd.

## Nieuwe scenario’s

De bestaande 21 snapshots blijven behouden. Toegevoegd:

- `a_sim negative control · 0.5 mm`, checkpoints `t=0,3 s`;
- `a_sim negative control · 1.5 mm`, checkpoints `t=0,3 s`.

Totaal:

\[
25\ \text{snapshots}.
\]

De twee extra runs controleren of een ogenschijnlijke closure van `L_ideal·2a_sim` rechtstreeks met de numerieke Biot–Savart-regularisatie meeschuift.

## Nieuwe gates

### ENGINE D9

Controleert:

- tien geregistreerde lengteklassen;
- eindige waarden in alle snapshots;
- correcte CANON-semantiek;
- identiteit van de gekalibreerde route met een zero-safe gemengde tolerantie:

\[
|\varepsilon|
\le
10^{-27}
+10^{-12}\max(|\delta Q|,|Q(t)|,|Q(0)|).
\]

### RESEARCH R16

Rangschikt de absolute route tegenover de absolute veldbracket.

### RESEARCH R17

Rangschikt de gekalibreerde route tegenover de gekalibreerde veldverandering.

### RESEARCH R18

Controleert tijdstrajectproportionaliteit over `t=0.5,1,2,3 s`. Een kandidaat mag niet alleen op één toevallig checkpoint dichtbij liggen.

### RESEARCH R19

Volgt iedere lengteklasse langs `N=128,192,256,384`.

### RESEARCH R20

Meet de gevoeligheid van `L_ideal·2a_sim` voor `a_sim=0.5,1.0,1.5 mm`.

### RESEARCH R21

No-fit toelatingsgate. Alleen `CANON_CARRIER`-lengtes kunnen semantisch worden toegelaten. Numerieke referentie- of controleschalen kunnen nooit door een schaalmatch tot `L_K` worden gepromoveerd.

### RESEARCH R22

Controleert de orthodoxe ropelengthreconstructie:

\[
L_K^{\rm direct}
\stackrel{?}{=}
16.371637\times2a_{\rm core}^{\rm reach}.
\]

Deze gate test of de directe centerline-integraal en de ideal-tube mapping dezelfde lengte representeren. Hij canoniseert niet `a_core=r_c`.

## Preflight-replay op de v7.6.19-export

De replay gebruikt de reeds gemeten v7.6.19-snapshots; de twee nieuwe `a_sim`-runs ontbreken daarin nog.

Voor de baseline bij `N=128`, `t=3 s`:

| lengteklasse | absolute `/ veld` | gekalibreerde `/ Δveld` |
|---|---:|---:|
| `RESOLVED_CURRENT` | 25.9204 | 47.5261 |
| `RESOLVED_REFERENCE` | 25.9204 | 47.5261 |
| `IDEAL_ASIM_DIAMETER` (`a_sim=1 mm`) | 1.18119 | 2.16577 |
| `TREFOIL_RC_DIAMETER_BENCHMARK` | `1.664×10^-12` | `3.052×10^-12` |
| `MINIMAL_NEUTRAL_LOOP` | `3.194×10^-13` | `5.856×10^-13` |
| `DISTANCE_CONTROL` | 29.2203 | 45.0389 |

De belangrijke voorlopige conclusie is:

- de fysisch juiste **lengteklasse** is de gesloten centerline `L_K`;
- die sluit met coefficient `1` nog niet: de gekalibreerde ratio is ongeveer `47.5`;
- `L_ideal·2a_sim` ligt numeriek dichtbij, maar is juist daarom de kritieke negatieve controle;
- de Research-Track trefoilwaarde `2·16.371637·r_c ≈ 4.61343×10^-14 m` ligt vele ordes te klein voor deze meterschaal-run;
- de laatste resolutiestap van de resolved-length route verandert in de replay nog circa `9.83%`;
- de tijdstrajectratio van de resolved-length route varieert circa `4.34%`, dus de trend is redelijk stabiel maar de amplitude sluit niet.

De echte v7.6.21-browserrun moet D9, R16–R22 en vooral de `a_sim`-negatieve controle definitief invullen.

## Niet gewijzigd

- RK4-integrator;
- CFL-begrenzing;
- Biot–Savart-kernel;
- circulatie;
- topology guard;
- formele veldbracket;
- bestaande Shapley-, normalisatie- en transfer-lawresultaten.

## Validatie

- JavaScript-syntax: PASS;
- module-selftest: PASS;
- 421 unieke DOM-id’s, geen duplicaten;
- schema `1.5`: aanwezig;
- tien lengteklassen: aanwezig;
- legacy `C_e`: niet aanwezig in zichtbare UI of machinevelden;
- mixed route-identity selftestscore: `8.12×10^-5 < 1`;
- ZIP-integriteit: te controleren bij packaging;
- volledige interactieve WebGL-run: niet uitgevoerd in de container.
