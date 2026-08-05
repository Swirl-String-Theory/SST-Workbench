# B0–B8 — axiale vortexbundel-testladder

## Modeldoel

De trefoil wordt behandeld als een lokaal vortexdefect in een achtergrond van rechte vortexbuizen die asymptotisch van \(z=-\infty\) naar \(z=+\infty\) lopen. De buizen hebben geen begin- of eindpunt in het rekendomein. In v0.3.0 zijn ze recht, oneindig en bevroren.

De vrije centrale apertuur wordt numeriek gedefinieerd als

\[
R_{\rm hole}^{\rm free}
=
\min_s \rho_\perp\!\left(X(s)\right)-a_K,
\]

waar \(a_K\) de gebruikte knot-core/regularisatieschaal is. De bundelradius is

\[
R_{\rm bundle}=\eta_h R_{\rm hole}^{\rm free}.
\]

## B0 — geïsoleerde controle

\[
\Gamma_{\rm hole}=0.
\]

Doel: reproduceer het bekende relative-equilibrium-residu van de statische ideal-knot-centerline.

## B1 — grote-radiuscontrole

\[
R_{\rm bundle}\gg R_{\rm hole}.
\]

Met vaste gemiddelde vorticiteit nadert het lokale veld een uniforme solid-body-rotatie. Dit moet de intrinsieke vormdynamica niet veranderen wanneer rigide rotatie correct wordt verwijderd.

## B2 — hole-matched continuum

\[
R_{\rm bundle}=R_{\rm hole}^{\rm free}.
\]

De achtergrond is een continue finite-radius Rankine-bundel. Dit is de minimale coarse-grained versie van de hypothese.

## B3 — radiusratio-sweep

\[
\eta_h\in\{0.5,0.75,1,1.25,1.5,2\}.
\]

Doel: zoek een open stabiliteitsgebied in plaats van één fijngetuned punt.

## B4 — co-/counter-rotating chirality

\[
\Gamma_{\rm hole}>0
\quad\text{versus}\quad
\Gamma_{\rm hole}<0.
\]

Trefoil en spiegel-trefoil worden beide getest. Een chirale respons moet van teken wisselen onder gelijktijdige spiegeling en circulatie-omkering.

## B5 — topologievergelijking

\[
0_1,\quad 3_1,\quad \overline{3_1},\quad 4_1.
\]

Dezelfde preregistreerde achtergrondprotocollen worden op meerdere topologieën toegepast.

## B6 — discrete buizen, twee interpretaties

### B6A — fysieke buizen

\[
\Gamma_{\rm tube}=\text{vast},
\qquad
\Gamma_{\rm hole}=N\Gamma_{\rm tube}.
\]

Veranderen van \(N\) verandert de fysieke totale flux. Dit is geen convergentietest.

### B6B — numerieke discretisatie

\[
\Gamma_{\rm hole}=\text{vast},
\qquad
\Gamma_{\rm tube}=\frac{\Gamma_{\rm hole}}{N}.
\]

Veranderen van \(N\) verfijnt alleen de representatie. De uitkomst moet convergeren naar de continue Rankine-bundel.

### B6C — volledige terugreactie

Status in v0.3.0:

\[
\boxed{\texttt{OPEN / NOT IMPLEMENTED}}
\]

De rechte buizen buigen nog niet onder de trefoil en onderling. De huidige resultaten gelden uitsluitend voor bevroren achtergrondbuizen.

## B7 — discretisatieconvergentie

Voor vaste \(R_{\rm bundle}\) en \(\Gamma_{\rm hole}\):

\[
N=1,7,19,37,61,91.
\]

De primaire convergentie-observabelen zijn:

\[
\delta_u(N)
=
\frac{|u_{\rm rms}^{(N)}-u_{\rm rms}^{\rm cont}|}
{|u_{\rm rms}^{\rm cont}|},
\]

\[
\delta_\epsilon(N)
=
\frac{|\epsilon_{\rm int}^{(N)}-\epsilon_{\rm int}^{\rm cont}|}
{|\epsilon_{\rm int}^{\rm cont}|}.
\]

## B8 — circulatiefase als klokdrager

De bundel definieert

\[
\Omega_\Gamma
=
\frac{\Gamma_{\rm hole}}
{2\pi R_{\rm bundle}^2},
\]

\[
\theta_\Gamma(t)=\Omega_\Gamma t,
\qquad
N_{\rm cycle}=\frac{\theta_\Gamma}{2\pi}.
\]

Deze fase is een klokdragerdiagnostiek. Zij is nog niet gelijkgesteld aan canonieke proper time.

## Primaire stabiliteitsgate

\[
\epsilon_{\rm int}
=
\frac{\|P_\perp(u_{\rm self}+u_{\rm bg}-u_{\rm rigid})\|}
{\|P_\perp u_{\rm self}\|}
<0.05.
\]

Deze normalisatie voorkomt dat een grote achtergrondstroom de residu kunstmatig klein maakt door alleen de noemer te vergroten.
