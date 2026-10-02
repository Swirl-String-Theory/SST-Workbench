# Methoden en formules

## 1. Centerline en geometrie

De gesloten centerline wordt op genormaliseerde booglengte geschreven als

\[
\mathbf X:S^1\rightarrow\mathbb R^3,
\qquad s\in[0,1).
\]

Na uniforme booglengteresampling berekent het pakket

\[
\mathbf t=\frac{d\mathbf X}{d\ell},
\qquad
\frac{d\mathbf t}{d\ell}=\kappa\mathbf n,
\qquad
\mathbf b=\mathbf t\times\mathbf n,
\qquad
\tau=-\frac{d\mathbf b}{d\ell}\cdot\mathbf n.
\]

De gerapporteerde thickness is een sampled proxy voor

\[
\Delta[\mathbf X]
=
\min\left\{
\min_s\frac{1}{\kappa(s)},
\frac12\min_{(s,\sigma)\in\mathrm{dc}}
\left|\mathbf X(s)-\mathbf X(\sigma)\right|
\right\}.
\]

Hij is niet gelijkgesteld aan een exact biarc- of polygonal-thicknesscertificaat.

## 2. Contactmap

Voor een punt \(\mathbf X(s)\) en een kandidaat \(\mathbf X(\sigma)\) wordt

\[
pt(s,\sigma)
=
\frac{\tfrac12\left|\mathbf X(s)-\mathbf X(\sigma)\right|}
{\left|\sin\theta(s,\sigma)\right|}
\]

geminimaliseerd, waarbij \(\theta\) de hoek is tussen de tangent in \(\sigma\)
en het koord. Een echt dubbel-kritisch contact moet tevens voldoen aan

\[
\mathbf c(s,\sigma)\cdot\mathbf t(s)=0,
\qquad
\mathbf c(s,\sigma)\cdot\mathbf t(\sigma)=0.
\]

Per samplepunt worden twee continue takken gevolgd. De lifts voldoen bij een
ideale graad-één tak aan

\[
\widetilde\sigma(s+1)=\widetilde\sigma(s)+1.
\]

De twee takken worden vervolgens getest als benaderde inversen:

\[
\tau\circ\sigma\simeq\mathrm{id},
\qquad
\sigma\circ\tau\simeq\mathrm{id}.
\]

## 3. Gesloten 9-billiard

Voor beide contacttakken zoekt het pakket afzonderlijk een seed \(s_0\) die

\[
\varepsilon_9(s_0)
=
 d_{S^1}\!\left(\sigma^9(s_0),s_0\right)
\]

minimaliseert. Een kandidaat is alleen primitief wanneer

\[
\min_{1\le k<9}
 d_{S^1}\!\left(\sigma^k(s_0),s_0\right)
\]

boven de lagere-periodedrempel blijft en de orbit negen afzonderlijke punten bevat.
Omdat de takken benaderde inversen moeten zijn, vereist H3 dat beide branches sluiten en dat hun negenpuntsorbitsets binnen een circulaire Hausdorfftolerantie samenvallen. De test zoekt een numerieke orbit; hij bewijst geen analytische periodiciteit.

## 4. Geometrische krachtbalans

Carlens mechanische bridge start met

\[
\frac{d}{d\ell}\left(T\mathbf t\right)+\mathbf F=0.
\]

Wanneer \(\mathbf F\) in het normaalvlak ligt, is \(T\) constant en

\[
T\kappa\mathbf n+\mathbf F=0.
\]

Voor twee contactkoorden lost het pakket lokaal

\[
F^{\mathrm I}\mathbf u_{\mathrm I}
+
F^{\mathrm O}\mathbf u_{\mathrm O}
+
\kappa\mathbf n
=0
\]

op. De onafhankelijke niet-lokale compatibiliteit is

\[
F^{\mathrm O}(s)
=
-F^{\mathrm I}(\sigma(s))\sigma'(s),
\]

met de inverse relatie

\[
F^{\mathrm I}(s)
=
-F^{\mathrm O}(\tau(s))\tau'(s).
\]

H4 gebruikt beide relaties. Punten waar de twee koorden vrijwel lineair afhankelijk
zijn worden als ill-conditioned gerapporteerd, niet stilzwijgend geïnterpoleerd in de
gate.

## 5. Regularized Biot–Savart-test

De geometrie- en contactlaag levert **geen** hydrodynamische parameters aan de
Biot–Savartfit. Voor segmentmiddens \(\mathbf M_j\) en segmentvectoren
\(\Delta\mathbf X_j\) gebruikt het pakket de Rosenhead-type kernel

\[
\mathbf u_a(\mathbf X_i)
=
\frac{\Gamma}{4\pi}
\sum_j
\frac{
\Delta\mathbf X_j\times(\mathbf X_i-\mathbf M_j)
}
{\left(\left|\mathbf X_i-\mathbf M_j\right|^2+a^2\right)^{3/2}}.
\]

Na verwijdering van de beste rigide translatie en rotatie is

\[
\varepsilon_{\rm RE}
=
\frac{\|\mathbf u_a-(\mathbf U+\boldsymbol\Omega\times\mathbf r)\|_2}
{\|\mathbf u_a\|_2}.
\]

H5 test of de centerline een benaderde relative equilibrium is.

## 6. Hamiltoniaanse variatiederivaat

Het regularized filament-energiefunctionaal is

\[
H_a[\mathbf X]
=
\frac{\rho_{\!f}\Gamma^2}{8\pi}
\oint\!\oint
\frac{d\mathbf X\cdot d\mathbf X'}
{\sqrt{|\mathbf X-\mathbf X'|^2+a^2}}.
\]

Het pakket berekent een centrale finite-difference-benadering van

\[
\frac{\delta H_a}{\delta\mathbf X}.
\]

De vormtest is

\[
\frac{\delta H_a}{\delta\mathbf X}
\stackrel{?}{=}
-T_{\rm eff}\kappa\mathbf n
+
\mathbf r,
\]

met één globale least-squareswaarde \(T_{\rm eff}>0\). Daarnaast wordt lokaal

\[
T_{\rm loc}(s)
=
-rac{
(\delta H_a/\delta\mathbf X)\cdot\mathbf n
}{\kappa}
\]

berekend. H6 vereist een kleine shape residual, positieve oriëntatie, beperkte
binormale lekkage en een beperkte variatiecoëfficiënt van \(T_{\rm loc}\).

Dit is een Hamiltoniaanse vormrespons. Het pakket identificeert
\(-\delta H/\delta\mathbf X\) niet met een dissipatieve gradient flow; de werkelijke
vortexkinematica wordt apart door H5 getest.

## 7. SI-schaal

Met geometrische thickness \(\Delta_{\rm geom}\) en gekozen fysieke thickness
\(\Delta_{\rm phys}\) is

\[
\ell_0=rac{\Delta_{\rm phys}}{\Delta_{\rm geom}}.
\]

Standaard geldt

\[
\Delta_{\rm phys}=r_c,
\qquad
\Gamma=2\pi r_c\mathbf v_{\!\boldsymbol{\circlearrowleft}}.
\]

De kracht-dimensies volgen uit

\[
\left[\rho_{\!f}\Gamma^2\right]
=
\mathrm N.
\]

Daarom heeft

\[
\frac{\rho_{\!f}\Gamma^2}{8\pi\ell_0}
\]

de dimensie \(\mathrm{N\,m^{-1}}\), passend bij een kracht per centerlinelengte.

## 8. Local/nonlocal guard

Voor H8 worden segmentparen met cyclische indexafstand
\(\le b_{\rm local}\) uit het energie- en snelheidsfunctionaal verwijderd. Deze split
is geen continuum-invariant. Daarom is H8 uitsluitend een guard tegen een ogenschijnlijk
succes dat volledig door nabije segmenten/local induction wordt gedragen.
