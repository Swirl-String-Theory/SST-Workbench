# Release notes v7.5.1 — SST horn/core-scheiding en eindige vortexbundel

**Basis:** v7.5. **Hoofdbestand:** `vortexring-lab-v7_5_1.html`.

Deze correctierelease verandert geen Canon-constanten. Zij herstelt de betekenis van die constanten in de simulator en sluit het achtergrondveld, de visualisatie en de passieve transportdiagnostiek op elkaar aan.

## 1. SST-schaalarchitectuur gecorrigeerd

De simulator onderscheidt nu drie verschillende lengtes:

\[
R_{\rm horn}=1.40897017\times10^{-15}\ {\rm m},
\]

de canonieke Compton-locked horn-/circulatieschaal;

\[
r_{\rm kern}<R_{\rm horn},
\]

de veel kleinere vaste, rotationele vortexkern uit de Research-Track profielinterpretatie; en

\[
a_{\rm sim},
\]

de numerieke regularisatie-, buis- en contactstraal van het centerline-filamentmodel.

Geen van deze drie wordt nog stilzwijgend gelijkgesteld. De oude variabele en UI-benaming `aPhys` is verwijderd. `r_kern` heeft bewust geen verzonnen standaardwaarde: de invoer blijft leeg totdat een onafhankelijke profiel- of variatieafleiding beschikbaar is.

De SST-profielinterpretatie is nu expliciet Rankine-achtig:

\[
v_\theta(r)=
\begin{cases}
\Omega_{\rm kern}r, & 0\le r\le r_{\rm kern},\\[3pt]
\Gamma/(2\pi r), & r>r_{\rm kern},
\end{cases}
\qquad
\Omega_{\rm kern}=\frac{\Gamma}{2\pi r_{\rm kern}^2}.
\]

De lokale vorticiteit is in de vaste kern

\[
\zeta_{\rm kern}=2\Omega_{\rm kern},
\]

terwijl de buitenstroming klassiek irrotationeel is: \(\nabla\times\mathbf u=0\) voor \(r>r_{\rm kern}\), afgezien van de ingesloten kernsingulariteit/topologie.

`OMEGA_CORE_SST` is verwijderd. De vaste canonieke waarde

\[
\omega_c=V_{\rm horn}/R_{\rm horn}
\]

heet nu `OMEGA_COMPTON_SST` en wordt expliciet als horn-/fasefrequentie behandeld, niet als lokale vorticiteit van de vaste kern.

## 2. SST-default en statuslabels

- De SST-start- en bundelpreset gebruiken de vaste/Rankine-filamentclosure (`core='vast'`).
- GP/NLSE blijft beschikbaar als conditionele alternatieve dun-filamentkalibratie, niet als “kernmodel per Canon”.
- Het informatiedeel verwijst nu naar **Canon v0.8.20 + Research Track**.
- De legacy Track-B-notatie \(\xi\leftrightarrow r_c\) wordt niet meer geïnterpreteerd als \(\xi\leftrightarrow R_{\rm horn}\); de nog open profielbrug is \(\xi\leftrightarrow r_{\rm kern}\).
- De Rankine display-similarity koppelt alleen \(a_{\rm sim}\), \(\Gamma\) en de gekozen macroscopische \(\Omega\). Zij legt geen fysische identificatie met \(r_{\rm kern}\) of \(R_{\rm horn}\) op.

## 3. Eindig vortexbundelveld

De bundelstraal is nu dynamisch consistent met het snelheidsveld. Voor een doorsnede met radius \(R_b(z)\) geldt:

\[
u_\theta(r,z)=
\begin{cases}
\Omega_b(z)r, & r\le R_b(z),\\[3pt]
\Omega_b(z)R_b(z)^2/r, & r>R_b(z).
\end{cases}
\]

Daarmee is de ingesloten circulatie buiten de bundel constant:

\[
\Gamma_{\rm enc}(z)=2\pi\Omega_b(z)R_b(z)^2.
\]

De eerdere implementatie gebruikte \(u_\theta=\Omega_b r\) in de gehele cilinder en liet de ingesloten circulatie ten onrechte doorgroeien buiten de gekozen bundelstraal.

Voor splay blijft

\[
\Omega_b(z)\propto\lambda(z)^{-2},
\qquad
R_b(z)\propto\lambda(z),
\]

zodat \(n_v(z)\pi R_b(z)^2\) en \(\Gamma_{\rm enc}(z)\) constant blijven. Dit blijft een kinematische Research-Track ansatz en geen stationaire Euler/HVBK-drukoplossing.

## 4. Gevulde bundelvisualisatie

De representatieve vortexlijnen liggen niet langer allemaal op één cilindrische schil. Zij worden quasi-uniform over de schijf verdeeld met

\[
\rho_i=\sqrt{\frac{i+1/2}{N}},
\qquad
\theta_i=i\,\pi(3-\sqrt5).
\]

Daardoor visualiseert de lijnenset dezelfde gevulde doorsnede als de coarse-grained dichtheid \(n_v\pi R_b^2\).

## 5. Eén achtergrondveld voor alle transportpaden

`backgroundVelocityAt()` is nu de gedeelde bron voor:

- filamentdynamica in `velocityCore()`;
- passieve tracers in `stepTracers()`;
- stroomlijnen in `fieldVelocityAt()`.

Daarmee tonen tracers en stroomlijnen voortaan hetzelfde bundelveld dat de filamenten aandrijft. De oude toestand waarin alleen de filamenten de SST-bundel voelden is verwijderd.

## 6. Betekenis van de verre bronlagen

De runtimebron is gelabeld als:

```text
analytic-finite-closed-loop-limit
```

Dit betekent: een analytische lokale coarse-grained limiet van zeer lange **gesloten** vortexlussen, waarvan de retourpaden ver buiten het simulatiedomein liggen. De simulator beweert niet dat open vortexlijnen uit verre knopen eindigen, en berekent nog geen expliciet Biot–Savartveld van knooplagen bij \(z=\pm L\).

Een toekomstige expliciete bronmodus moet gesloten lussen, retourpaden, bronafstand en een convergentietest tegen het analytische bundelveld bevatten. Deze release voegt daar geen schijnimplementatie voor toe.

## 7. Nieuwe zelftests

- **T0j:** \(R_{\rm horn}\), \(r_{\rm kern}\) en \(a_{\rm sim}\) blijven onderscheiden; de hornlocatie ligt in het irrotationele buitenprofiel.
- **T0k:** continuïteit van de Rankine-kernsnelheid naar het \(1/r\)-buitenveld en \(\zeta_{\rm kern}=2\Omega_{\rm kern}\).
- **T9f:** continu snelheidsveld op \(R_b\) en constante buiten-circulatie.
- **T9g:** gedeeld achtergrondveld voor filament-, tracer- en stroomlijntransport.
- **T9h:** gevulde-schijfsampling met \(\langle\rho^2\rangle=1/2\).
- **T9i:** expliciete bronprovenance `analytic-finite-closed-loop-limit`.

Bestaande T0–T9e, T8-frame-equivalentie, ACN-hotfix, ModelLog 0.2, contactvloer en deterministische stepper blijven aanwezig.

## 8. Validatie

Uitgevoerd op de gepatchte build:

```text
VALIDATOR: PASS (275 unieke IDs)
node --check: groen
```

Nog verplicht in een lokale browser/WebGL-omgeving:

```bash
npm i puppeteer
node browser-smoke-v7_5_1.mjs vortexring-lab-v7_5_1.html
```

## 9. Bewuste beperkingen

- `r_kern` is een Research-Track invoer en stuurt de centerline-integrator nog niet.
- De radiale vaste-kern/irrotationele-profielvergelijking wordt diagnostisch geëvalueerd, niet als resolved PDE opgelost.
- De verre gesloten bronlussen en fictieve knooplagen worden niet expliciet gediscretiseerd.
- Splay heeft nog geen drukgesloten continuumoplossing.
- `a_sim` blijft de straal die de LIA-logaritme, regularisatie, visualisatie en contactdetectie aanstuurt.
