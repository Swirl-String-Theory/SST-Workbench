# 03 — Variationale selectie van de core-radiusratio \(\chi\)

**Status:** `[THEOREM TARGET / RESEARCH]`

## 1. Het centrale probleem

Definieer:

\[
\chi
=
\frac{a_{\rm core}}{r_c}.
\]

In de bestaande lokale action/neck closure ontstaat:

\[
\beta_Q(\chi)
=
\frac{\chi^3}{2}
\exp\!\left[\frac{\pi^2\chi^6-1}{4}\right].
\]

Daaruit volgt in de betreffende calibrated branch:

\[
\frac{c_T}{c}
=
2\alpha\beta_Q.
\]

De selector is niet numeriek triviaal, maar de fysieke uitkomst is niet uniek zolang \(\chi\) vrij blijft.

## 2. Gevoeligheid

De logaritmische gevoeligheid is:

\[
\frac{d\ln\beta_Q}{d\ln\chi}
=
3+
\frac{3\pi^2}{2}\chi^6.
\]

Bij \(\chi=1\):

\[
\frac{d\ln\beta_Q}{d\ln\chi}
\approx17.804.
\]

Een procent verandering in \(\chi\) verandert \(\beta_Q\) lokaal dus met ongeveer \(17.8\%\). Dit maakt elke achteraf gekozen core-radius onaanvaardbaar als voorspelling.

## 3. Wat moet worden gevarieerd

Een minimum viable finite-core functionaal is:

\[
\mathcal E[\gamma,a,f]
=
E_{\rm kin}^{(a,f)}[\gamma]
+
T(a,f)L[\gamma]
+
B(a,f)\oint\kappa^2ds
+
E_{\rm twist}[\gamma,f]
+
E_{\rm core}[a,f],
\]

onder constraints:

\[
\Gamma=\Gamma_0,
\qquad
V_{\rm tube}=V_0,
\qquad
\operatorname{reach}(\gamma)\ge a,
\qquad
\text{topologie}=K.
\]

Hier is \(f(r/a)\) het dimensieloze coreprofiel.

De variatie moet minstens omvatten:

- centerline \(\gamma\);
- core-radius \(a\);
- profielvorm \(f\);
- twistverdeling;
- neck/adjacencygeometrie;
- density ratio indien die niet uit dezelfde actie volgt.

## 4. Euler--Lagrange-targets

De eerste variatie moet leiden tot:

\[
\frac{\delta\mathcal E}{\delta\gamma}=0,
\qquad
\frac{\partial\mathcal E}{\partial a}=0,
\qquad
\frac{\delta\mathcal E}{\delta f}=0.
\]

De tweede variatie moet positief zijn buiten symmetrie- en constraintnulmoden:

\[
\delta^2\mathcal E
\ge0.
\]

Pas dan kan een gevonden \(\chi_*\) als selector worden gebruikt.

## 5. Vereiste dimensionless reduction

Schrijf:

\[
\mathbf X=r_*\mathbf x,
\qquad
a=r_*\chi,
\qquad
E=E_*\mathcal E^*.
\]

De dimensieloze variatie moet de vorm hebben:

\[
\mathcal E^*
=
\mathcal F_K[\mathbf x,\chi,f;\lambda_1,\lambda_2,\ldots],
\]

waar alle \(\lambda_i\) vooraf uit de microdynamica volgen. Een targetwaarde van \(c\), \(\alpha\) of \(m_e\) mag niet worden gebruikt om \(\chi\) te kiezen.

## 6. Numeriek programma

### C0 — Profielbibliotheek

Preregistreer minimaal:

- Rankine;
- Gaussian;
- Rosenhead-equivalent;
- Gross--Pitaevskii-like healing profile.

### C1 — Ringbenchmark

Voor iedere profielbranch:

- energie versus \(a/R\);
- translatie­snelheid;
- Kelvin-wave dispersion;
- vergelijking met bekende asymptotiek.

### C2 — Trefoilvariatie

Optimaliseer tegelijk:

- centerline;
- reach;
- core-radius;
- profielparameter;
- twist.

### C3 — Uniciteit en bifurcatie

Onderzoek of \(\partial_aE=0\) één, meerdere of geen wortels heeft. Rapporteer bifurcaties in plaats van één voorkeurswortel te selecteren.

### C4 — Robuustheid

Een fysieke \(\chi_*\) moet stabiel zijn onder:

- meshverfijning;
- quadratuurorde;
- domain truncation;
- twee admissibele regularisaties;
- kleine profielperturbaties.

### C5 — Pas daarna \(\beta_Q\) en \(c_T\)

Bereken:

\[
\beta_Q(\chi_*),
\qquad
c_T(\chi_*),
\]

zonder retuning.

## 7. Falsifiers

De selectorroute faalt wanneer:

1. geen stationair \(a\) bestaat;
2. het stationaire punt een maximum of saddle is;
3. \(\chi_*\) regulatorafhankelijk blijft;
4. verschillende topologieën elk een vrij aangepaste \(\chi\) nodig hebben;
5. de density/neck law achteraf wordt afgestemd;
6. \(c_T=c\) alleen ontstaat wanneer \(c\) in de selectie is gebruikt;
7. de gevonden core de reachconstraint schendt;
8. de toestand dynamisch instabiel is.

## 8. Verdedigbaar succescriterium

\[
\boxed{
\chi_*
\text{ is een unieke, stabiele dimensieloze minimizer van één vastgelegde actie.}
}
\]

Pas daarna mag \(\chi_*\) een echte input voor Route I, \(\beta_Q\), \(c_T\) of particle-sectorberekeningen worden.
