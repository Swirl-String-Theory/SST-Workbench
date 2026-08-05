# 01 — Dynamisch gecertificeerde knooptoestanden en dimensieloze ratio's

**Status:** `[RESEARCH / HOOGSTE PRIORITEIT]`  
**Hoofddoel:** één dimensieloze SST-observable produceren die vooraf is vastgelegd, numeriek convergeert, geen targetconstante hergebruikt en extern kan worden gebenchmarkt.

## 1. Waarom dit de eerste track is

De bestaande SST-constantenketen is grotendeels gekalibreerd. Daardoor zijn absolute voorspellingen voor massa, \(\alpha\), \(G\) en spectra voorlopig kwetsbaar voor circulariteit. Een dimensieloze verhouding kan daarentegen alle absolute schalen laten wegvallen.

De aanbevolen eerste targets zijn:

\[
\mathcal R_E(K)
=
\frac{E_K}{E_{0_1}},
\qquad
\mathcal R_\Omega(K)
=
\frac{\Omega_K}{\Omega_{0_1}},
\]

of een kinematische vervanger zolang echte periodic orbits nog ontbreken:

\[
\mathcal R_{\rm rigid}(K)
=
\frac{\sqrt{(U_K/R_K)^2+|\boldsymbol\Omega_K|^2}}
{\sqrt{(U_{0_1}/R_{0_1})^2+|\boldsymbol\Omega_{0_1}|^2}}.
\]

Deze observabelen kunnen worden opgezet met:

\[
\Gamma=1,
\qquad
\rho=1,
\qquad
L=2\pi,
\qquad
\epsilon=a_{\rm core}/R=\text{vast}.
\]

Daarmee geldt formeel:

\[
\frac{\partial \mathcal R}{\partial \alpha}
=
\frac{\partial \mathcal R}{\partial m_e}
=
\frac{\partial \mathcal R}{\partial G}
=0.
\]

## 2. Huidige diagnose

Een ideal-knot centerline is een geometrische benchmark, niet automatisch een dynamisch evenwicht. De eerdere Biot--Savart-audit vond een zeer klein ringresidu, maar veel grotere residuen voor de statische trefoil en figure-eight.

De relevante scheiding is:

\[
\text{ropelength criticality}
\neq
\text{relative equilibrium}
\neq
\text{lineaire stabiliteit}
\neq
\text{KAM-stabiliteit}.
\]

Daarom moet de dynamische toestand worden gevonden door de dynamica zelf, niet door een ideal-knotbestand simpelweg als deeltje te labelen.

## 3. Governing model dat vooraf moet worden bevroren

De eerste numerieke ladder gebruikt een geregulariseerde filamentdynamica:

\[
\dot{\mathbf X}(s)
=
\frac{\Gamma}{4\pi}
\oint
\frac{d\mathbf X(s')\times[\mathbf X(s)-\mathbf X(s')]}
{\left(|\mathbf X(s)-\mathbf X(s')|^2+\epsilon^2\right)^{3/2}}.
\]

Dit is een diagnostisch model. Een latere promotie vereist een finite-core Hamiltoniaan of PDE met één verklaard coreprofiel.

Alle volgende elementen moeten vóór vergelijking worden vastgelegd:

- corekernel;
- dimensieloze core-radius \(\epsilon\);
- normalisatieprotocol;
- centerlinebron;
- remeshingregel;
- integrator;
- tijdstap;
- residual- en recurrence-toleranties;
- toegestane symmetriequotienten.

## 4. Relative-equilibrium fit

Een relatieve evenwichtstoestand voldoet modulo tangentiële gauge aan:

\[
\mathbf u_i
\approx
\mathbf U
+
\boldsymbol\Omega\times(\mathbf X_i-\mathbf X_c)
+
\lambda_i\mathbf t_i.
\]

Projecteer op het normaalvlak:

\[
P_i=I-\mathbf t_i\mathbf t_i^{\mathsf T}.
\]

De gebruikte residual is:

\[
\epsilon_{\rm rel}
=
\frac{
\left\|P_i\left[
\mathbf u_i-
\mathbf U-
\boldsymbol\Omega\times(\mathbf X_i-\mathbf X_c)
\right]\right\|_2
}
{
\|P_i\mathbf u_i\|_2
}.
\]

Preregistreerde eerste gates:

\[
\epsilon_{\rm rel}<5\%
\quad\text{voor kandidaatstatus},
\]

\[
\epsilon_{\rm rel}<1\%
\quad\text{voor een serieuze vervolgsolve}.
\]

Deze grenzen zijn numerieke werkgrenzen, geen canonieke natuurconstanten.

## 5. Eerste observabelen

Het pakket berekent al:

### 5.1 Energieproxy

\[
E_\epsilon
=
\frac{\Gamma^2}{8\pi}
\oint\oint
\frac{\mathbf t(s)\cdot\mathbf t(s')}
{\sqrt{|\mathbf X(s)-\mathbf X(s')|^2+\epsilon^2}}
\,ds\,ds'.
\]

Bij dezelfde \(\Gamma\), normalisatie en \(\epsilon\) is

\[
\mathcal R_E(K)=E_\epsilon(K)/E_\epsilon(0_1)
\]

dimensieloos.

### 5.2 Rigid-motion rate

\[
\Omega_{\rm rigid}^*
=
\sqrt{
\left(\frac{|\mathbf U|}{R}\right)^2
+
|\boldsymbol\Omega|^2
}.
\]

### 5.3 Deformation rate

\[
\Omega_{\rm def}^*
=
\frac{1}{R\sqrt N}
\left\|P_i\left(\mathbf u_i-\mathbf u_i^{\rm rigid}\right)\right\|_2.
\]

### 5.4 Hydrodynamische impuls

\[
\mathbf I
=
\frac{\Gamma}{2}
\oint \mathbf X\times d\mathbf X.
\]

### 5.5 Bending integral

\[
B_K
=
\oint\kappa^2ds.
\]

### 5.6 Recurrence error

Na translatie, optimale rotatie en cyclische parameter-shift:

\[
\epsilon_{\rm rec}(T)
=
\min_{R,\Delta s}
\frac{
\|\mathbf X(T,s)-R\mathbf X(0,s+\Delta s)\|_{L^2}
}{R_{\rm rms}}.
\]

## 6. Numerieke ladder

### D0 — Sanity benchmark

- ronde ring;
- vergelijking met bekende LIA-snelheid;
- energy en length drift;
- residual onder verfijning.

### D1 — Atlasdiagnostiek

- ideal \(3_1\);
- spiegel-\(3_1\);
- ideal \(4_1\);
- drie corekernels;
- resolutieladder.

### D2 — Relative-state solve

Optimaliseer centerlinecoördinaten en rigid-motionparameters tegelijk:

\[
\min_{\mathbf X,\mathbf U,\boldsymbol\Omega,\lambda}
\epsilon_{\rm rel}^2
+
\mu_L(L-L_0)^2
+
\mu_V(V_{\rm tube}-V_0)^2
+
\text{clearance barrier}.
\]

### D3 — Periodic/relative-periodic solve

Los op:

\[
\Phi_T(\mathbf X_0)
=
R\mathbf X_0(\cdot+\Delta s)+\mathbf a
\]

met Newton--Krylov of multiple shooting.

### D4 — Tangent-linear operator

Bereken de monodromiematrix:

\[
\delta\mathbf X(T)
=
\mathcal M_T\delta\mathbf X(0).
\]

### D5 — Floquet- en Krein-audit

- verwijder symmetrie-nullmoden;
- bepaal \(\mu_j\);
- controleer \(|\mu_j|\);
- bepaal Krein-signatuur;
- test regulatorstabiliteit.

### D6 — Externe benchmark

Vergelijk exact dezelfde dimensieloze observable met:

- een onafhankelijke Biot--Savart-code;
- een Gross--Pitaevskii-simulatie;
- een finite-core Euler-solver;
- of een gecontroleerd vortexexperiment.

## 7. Hard falsifiers

De track faalt voor een gekozen modelbranch wanneer één van de volgende onder verfijning blijft bestaan:

1. geen ringbenchmarkconvergentie;
2. geen kleine relative-equilibrium-residual voor de gekozen knoop;
3. topologyverlies of reconnection zonder verklaarde niet-ideale wet;
4. sterke kernelafhankelijkheid van de ratio;
5. geen tijdstap- of resolutieconvergentie;
6. een niet-triviale Floquetmultiplier met \(|\mu|>1+\delta\);
7. seculiere energy/action drift;
8. ratio verandert na kleine admissibele remeshingwijziging;
9. parameterretuning per topologie;
10. targetdata wordt gebruikt om de branch te kiezen.

## 8. Succescriterium voor de eerste echte SST-voorspelling

Een minimale successituatie is:

\[
\boxed{
\mathcal R_E(3_1)
\text{ of }
\mathcal R_\Omega(3_1)
}
\]

met:

- vooraf bevroren model;
- geen CODATA-input;
- \(<1\%\) numerieke onzekerheid;
- stabiliteit onder twee corekernels;
- onafhankelijke externe bevestiging zonder retuning.

Dat bewijst nog niet dat het elektron een trefoil is. Het bewijst wel dat de SST-knoopdynamica een out-of-sample voorspellende inhoud heeft.

## 9. Implementatiestatus in v0.1.0

Reeds aanwezig:

- AB-ideal-parser;
- ring/trefoil/mirror/figure-eight;
- Biot--Savartkernels;
- relative-motion-fit;
- residual;
- energyproxy;
- impuls;
- RK4-evolutie;
- recurrence error;
- ratio- en convergentie-output.

Nog te bouwen:

- constrained equilibrium optimizer;
- exacte segment-dcsd/reach;
- Newton--Krylov periodic-orbit solve;
- tangent-linear JVP;
- Arnoldi/Floquet;
- Krein-signaturen;
- KAM frequency map;
- externe backendinterface.
