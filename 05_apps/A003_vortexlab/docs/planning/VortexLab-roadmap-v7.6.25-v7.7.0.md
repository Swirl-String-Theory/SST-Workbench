# VortexLab Research Track roadmap — v7.6.25 tot v7.7.0

## Uitgangspunt na v7.6.24

V7.6.24 scheidt:

- lokale mutual velocity;
- globale rigid-bodyrespons;
- intrinsieke rigid-rotationprojectie;
- embeddinggevoeligheid;
- topologyverschillen;
- formele kinematische Swirl-Clockveldroute.

Geen bestaande \(\kappa_{\rm geom}\)-factor is gecanoniseerd of naar de solver gekoppeld.

## v7.6.25 — Continue DCSD/reach-solver

Doel: vervang de stride- en tolerantiebased discrete reachschatter.

Implementatie:

- coarse chord candidate search;
- continue optimalisatie in \((s,t)\);
- expliciete orthogonaliteitsresiduen;
- lokale-neighbouruitsluiting op arclength;
- afzonderlijke curvature- en DCSD-limiet;
- dominant-limit provenance;
- N=128–1536 audit op unknot, \(3_1\), \(4_1\), \(5_1\), \(5_2\), \(6_1\).

Acceptatie: diameter/reachfout <0.5% en niet systematisch groeiend met N.

## v7.6.26 — Signed lokale Swirl-Clockroute

Gebruik puntgewijs:

\[
v_{\rm eff}^2(s)=
\left|
 v_{\!\circlearrowleft}^{\ast}\hat{\mathbf e}(s)
 +\mathbf u_{\rm mutual}(s)
\right|^2.
\]

Rapporteer signed mean, RMS, positieve/negatieve arclengthfracties, extrema, A/B-pariteit en chiraliteit.

De bestaande \(\pm u_{\rm RMS}\)-route blijft alleen een symmetrische envelope.

## v7.6.27 — Afstand, oriëntatie en multipolen

Bevroren geometrieën voor:

\[
d/L_K=1.1,1.25,1.5,2,3,4.
\]

Voeg laterale offset, kantelhoek, co-/contraoriëntatie en spiegeling toe. Reserveer ongeziene scenario’s als holdout.

## v7.6.28 — Observable-separation cleanup

Hernoem legacyvelden:

- `phaseLogRatio` → `rigidResponseLogRatio`;
- `omegaBody` → `omegaRigidCenterline`;
- `fieldLogMin/Max` → `kinematicClockEnvelopeMin/Max`;
- `v_def` → `centerlineDeformationResidual`.

UI-blokken:

1. KINEMATIC CLOCK;
2. RIGID CARRIER RESPONSE;
3. GEOMETRIC THICKNESS;
4. INTERNAL PHASE — NOT YET RESOLVED.

## v7.6.29 — Passief Bishop-material frame

Voeg per centerlinepunt toe:

\[
(\hat{\mathbf t},\hat{\mathbf n}_1,\hat{\mathbf n}_2),
\qquad
\theta_{\rm int}(s,t).
\]

Ongestoorde frequentie:

\[
\dot\theta_0=\omega_c=
\frac{v_{\!\circlearrowleft}^{\ast}}{r_c}.
\]

Nog geen externe modulatie of solverfeedback.

## v7.6.30 — Externe velocity-gradienttensor

Bereken:

\[
G_{ij}=\partial_j u_{{\rm mutual},i},
\qquad
S=\tfrac12(G+G^T),
\qquad
W=\tfrac12(G-G^T).
\]

Gates voor incompressibiliteit, stencilconvergentie, parameterisatie en resolutie.

## v7.7.0 — Confirmatoire beslismijlpaal

Een afgeleide interne klokwet moet slagen op:

- continuumconvergentie;
- static null;
- A/B-pariteit;
- chiraliteitsvoorspelling;
- afstand- en oriëntatieholdouts;
- meerdere topologieën en embeddings;
- `a_sim`-onafhankelijkheid;
- independently derived coefficients.

Geldige uitkomsten:

\[
\boxed{\text{een interne klokwet doorstaat alle holdouts}}
\]

of:

\[
\boxed{\text{de onderzochte routes worden reproduceerbaar verworpen}.}
\]
