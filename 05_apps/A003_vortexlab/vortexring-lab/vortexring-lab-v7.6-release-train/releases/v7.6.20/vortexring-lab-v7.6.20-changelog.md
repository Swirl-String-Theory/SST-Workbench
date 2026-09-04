# VortexLab v7.6.20 — canonieke `v↺*`-notatie in de transfer-lawbenchmark

**Versie:** 7.6.20  
**Parent:** 7.6.19  
**Basis:** 7.5.3  
**Schema proxy/decomposition:** `vortexlab-spec-clock-proxy-decomposition/1.4`

## Aanleiding

V7.6.19 gebruikte in het nieuwe transfer-lawregister een verouderde snelheidsletter en een gelijknamige machine-key. Dat was niet in lijn met de actuele SST CANON en Rosetta-huisstijl.

De actuele bronbestanden zijn opnieuw gecontroleerd:

- `SST_CANON-v0.8.20.tex` definieert
  \[
  v_{\!\boldsymbol{\circlearrowleft}}^{\ast}
  =
  \left\lVert\mathbf v_{\!\boldsymbol{\circlearrowleft}}\right\rVert
  \]
  als de **canonieke scalaire karakteristieke swirl-snelheid**;
- dezelfde canon reserveert de vectornotatie zonder argumenten voor de canonieke carrier velocity en verbiedt gebruik daarvan als onbeperkt lokaal veld;
- `SST_CANON-v0.8.20-research-track.tex` gebruikt
  \(\mathbf u_{\!\boldsymbol{\circlearrowleft}}(\mathbf x,t)\)
  voor het lokale snelheidsveld en benadrukt dat een lokale modesnelheid niet stilzwijgend gelijk is aan de canonieke scalaire snelheid;
- de numerieke canonwaarde blijft
  \[
  v_{\!\boldsymbol{\circlearrowleft}}^{\ast}
  =1.09384563\times10^6\ \mathrm{m\,s^{-1}}.
  \]

## Canonieke scheiding

V7.6.20 hanteert nu consequent:

| Rol | Notatie | Machine-key |
|---|---|---|
| Canonieke scalaire karakteristieke swirl-snelheid | \(v_{\!\boldsymbol{\circlearrowleft}}^{\ast}\) | `vChar` |
| Lokaal swirl-snelheidsveld | \(\mathbf u_{\!\boldsymbol{\circlearrowleft}}(\mathbf x,t)\) | bestaande lokale veldarrays |
| Interne canonieke constante | — | `V_CHAR_SST` |

Er is **geen compatibiliteitsalias** toegevoegd. Oude exportschema’s blijven historische records; nieuwe exports gebruiken uitsluitend de canonieke key.

## Aangepaste benchmarkvraag

De transfer-lawbenchmark rapporteert nu:

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
 v_{\!\boldsymbol{\circlearrowleft}}^{\ast},
 r_c
\right)
}
\]

De advectieve kandidaten zijn daarmee:

\[
\Delta\Omega\frac{a}{v_{\!\boldsymbol{\circlearrowleft}}^{\ast}},
\qquad
\Delta\Omega\frac{L}{v_{\!\boldsymbol{\circlearrowleft}}^{\ast}},
\qquad
\Delta\Omega\frac{d}{v_{\!\boldsymbol{\circlearrowleft}}^{\ast}},
\qquad
\Delta\Omega\frac{r_c}{v_{\!\boldsymbol{\circlearrowleft}}^{\ast}}.
\]

Ook de geometrisch gedempte advectieve kandidaat en de Buckingham-monomiaal gebruiken nu dezelfde canonieke snelheid.

## Code- en exportwijzigingen

1. `V_HORN_SST` is hernoemd naar `V_CHAR_SST`.
2. De transfer-lawinput gebruikt `vChar`.
3. De exponentregisters gebruiken `vChar`.
4. JSON exporteert `characteristicSpeed` met:
   - `jsonKey: "vChar"`;
   - `symbol: "v↺*"`;
   - de canonieke LaTeX-notatie;
   - de numerieke waarde;
   - de expliciete scheiding van het lokale veldsymbool.
5. `transferLaws.carrier.A.inputs`, `transferLaws.carrier.B.inputs` en `transferLaws.constants` bevatten uitsluitend `vChar`.
6. Labels, formules, TXT, JSON en CSV gebruiken zichtbaar `v↺*`.
7. Het schemasuffix is verhoogd van `1.3` naar `1.4`, omdat de JSON-key bewust incompatibel is gewijzigd.

## Nieuwe ENGINE-gate D8

D8 valideert per browserrun:

- alle elf kandidaatwetten hebben een exponentveld `vChar`;
- geen legacy snelheidkey staat in het register;
- alle snapshotinputs bevatten `vChar`;
- het constants-object bevat `vChar`;
- de zichtbare formule- en labelregistratie bevat uitsluitend de canonieke notatie.

Verwacht verdict:

\[
\boxed{\mathrm{D8=PASS}}
\]

Een D8-FAIL is uitsluitend een schema-/notatiefout en geen fysische falsificatie.

## Numerieke invariantie

Er zijn geen fysische formules, invoerwaarden, toleranties, solverstappen of researchcriteria gewijzigd.

De elf wetten zijn tegen de echte v7.6.19-browserexport herberekend met `vChar`. De grootste relatieve numerieke afwijking ten opzichte van de bestaande resultaten was uitsluitend floating-pointniveau:

\[
1.48\times10^{-16}.
\]

Voor de twee relevante kandidaten bleef de waarde exact gelijk binnen de opgeslagen precisie:

\[
\Delta\Omega\frac{L}{v_{\!\boldsymbol{\circlearrowleft}}^{\ast}}
=-1.0870531006428152\times10^{-21},
\]

\[
\Delta\Omega\frac{d}{v_{\!\boldsymbol{\circlearrowleft}}^{\ast}}
=-1.225444442696284\times10^{-21}.
\]

De wijziging is dus een canonieke notatie- en schemaherstelpatch, geen herfit en geen verandering van de wetenschappelijke uitkomst.

## Validatie

- inline JavaScript: syntax geldig;
- elf transferwetten aanwezig;
- elf wetten dimensioneel \(L^0T^0\);
- elf coëfficiënten exact `1`;
- alle exponentregisters gebruiken `vChar`;
- geen legacy snelheidssymbool of zelfstandige legacy machine-key in het HTML-bestand;
- `V_HORN_SST` volledig verwijderd;
- schema `1.4` aanwezig;
- parent `7.6.19`, base `7.5.3`;
- numerieke replay tegen de v7.6.19-export geslaagd.

## Wetenschappelijke status

De notatiecorrectie verandert het v7.6.19-verdict niet:

\[
\boxed{\mathrm{ENGINE=PASS}}
\qquad
\boxed{\mathrm{RESEARCH=FAIL}}
\]

De kandidaten \(\Delta\Omega L/v_{\!\boldsymbol{\circlearrowleft}}^{\ast}\) en \(\Delta\Omega d/v_{\!\boldsymbol{\circlearrowleft}}^{\ast}\) blijven interessant als trenddiagnose, maar zijn nog niet resolutiegeconvergeerd en vormen geen afgeleide klokwet.
