# 05 — Atomaire envelope als zelfstandig eigenprobleem

**Status:** `[RESEARCH / LITERAL CORE MODEL REJECTED]`

## 1. Waarom een aparte envelope nodig is

De letterlijke interpretatie waarin de microscopische vortexknoop zelf tot de Bohrstraal uitzet, botst met:

- de enorme schaalverhouding;
- de te kleine actie per core-circulatie;
- het ontbreken van een natuurlijke \(n\)-ladder bij vaste circulatie;
- het ontbreken van \(\ell,m,j\)-state counting;
- het risico dat de bekende Bohrquantisatie simpelweg opnieuw wordt ingevoerd.

De logisch overblijvende structuur is:

\[
\boxed{
\text{compacte topologische kern}
+
\text{uitgestrekte gebonden envelope-eigenmodus}.
}
\]

## 2. Minimale veldinhoud

Neem een envelopeveld \(\Psi\) gekoppeld aan een compacte knoopbron \(K\):

\[
\Psi(\mathbf x,t)
=
\psi(\mathbf x)e^{-i\omega t}.
\]

Een algemene eigenvergelijking is:

\[
\mathcal H_K\psi_n
=
\mathcal E_n\psi_n.
\]

De operator mag niet achteraf worden gekozen om het waterstofspectrum te reproduceren. Een kandidaat is:

\[
\mathcal H_K
=
-\nabla\cdot A_K(\mathbf x)\nabla
+
V_K(\mathbf x)
+
\mathcal T_K
+
\mathcal S_K,
\]

waar:

- \(A_K\): effectieve stiffness/inertia tensor;
- \(V_K\): uit de knoopbron afgeleid potentiaal;
- \(\mathcal T_K\): torsie/heliciteitskoppeling;
- \(\mathcal S_K\): spinoriale of double-coverstructuur, indien afgeleid.

## 3. Wat zelfstandig moet ontstaan

Een succesvolle operator moet zonder Bohrinput genereren:

\[
E_{n\ell mj},
\qquad
n,\ell,m,j,
\]

plus:

- degeneracies;
- parity;
- selection rules;
- transition matrix elements;
- continuum threshold;
- bound-state normalization;
- respons op externe velden.

De leading Coulombachtige \(-1/r\)-vorm alleen is onvoldoende. Ook de action quantum en boundary conditions moeten uit SST volgen.

## 4. Geen verborgen Bohrquantisatie

De volgende stap is niet toegestaan als afleiding:

\[
\Gamma_n=n\Gamma_{\rm env}
\quad\Rightarrow\quad
r_n\propto n^2,
\quad
E_n\propto-n^{-2},
\]

wanneer \(\Gamma_n=n\Gamma\) slechts wordt gepostuleerd. Dat is precies de quantisatieregel die verklaard moet worden.

Een echte route moet een eigenvalue condition leveren, bijvoorbeeld:

\[
\det\mathcal M(\mathcal E)=0,
\]

of een single-valuedness/topological boundary condition die discrete waarden afdwingt.

## 5. Mogelijke operatorroutes

### 5.1 Sturm--Liouville envelope

Na symmetriereductie:

\[
-\frac{d}{dr}
\left[p(r)\frac{du}{dr}\right]
+
q_{K\ell}(r)u
=
\lambda w(r)u.
\]

De functies \(p,q,w\) moeten uit de mediumactie volgen.

### 5.2 Link-field bound modes

Een compacte knoop kan een defect in een link/torsion field vormen. Lineariseer rond de defectachtergrond:

\[
\delta^2S_K\,\psi_n
=
\lambda_n\psi_n.
\]

Dan zijn de atomaire modes normale modes van de defectachtergrond.

### 5.3 Floquet-bound states

Wanneer de kern periodiek intern beweegt, kan de envelope een Floquetprobleem zijn:

\[
\left(\mathcal H_K(t)-i\partial_t\right)u_\alpha(t)
=
\varepsilon_\alpha u_\alpha(t),
\qquad
u_\alpha(t+T)=u_\alpha(t).
\]

### 5.4 Topological bundle route

Spin en half-integer structuur mogen alleen worden ingevoerd via een daadwerkelijk afgeleide bundle/double-coverrepresentatie, niet via analogie met een draaiende ring.

## 6. Numerieke ladder

### A0 — Operatorprovenance

Leid \(\mathcal H_K\) af uit dezelfde actie als de knoopachtergrond.

### A1 — Sferisch/axisymmetrisch benchmarkprobleem

Test self-adjointness, spectrum en continuum threshold.

### A2 — Ring versus trefoil

Bereken het verschil in envelope-spectrum door topologie en anisotropie.

### A3 — Quantum-number generation

Controleer of de operator vanzelf een complete set labels en degeneracies levert.

### A4 — Transition operator

Leid de koppeling aan een propagating torsion/link mode af en bereken:

\[
\langle f|\mathcal O_{\rm rad}|i\rangle.
\]

### A5 — Preregistered spectral ratios

Test eerst dimensionless verhoudingen, bijvoorbeeld:

\[
\mathcal R_{21}
=
\frac{E_2-E_1}{E_3-E_1},
\]

zonder absolute energiecalibratie.

### A6 — Pas daarna absolute schaal

Gebruik maximaal één onafhankelijke schaalcalibratie en voorspel ongebruikte lijnen.

## 7. Hard gates

1. \(\mathcal H_K\) is self-adjoint of heeft een verklaarde niet-Hermitische fysica;
2. spectrum is onderaan begrensd;
3. bound states zijn normaaliseerbaar;
4. quantum numbers ontstaan uit symmetrie/operatorstructuur;
5. geen Bohr-radius, Rydberg of \(\alpha\) in de selector;
6. transition rules volgen uit matrixelementen;
7. spectrum convergeert onder mesh/domain refinement;
8. kern- en envelope-schaal blijven onderscheiden;
9. dezelfde operator werkt voor meerdere levels;
10. fine/recoil/QED-achtige correcties worden niet als vrije fit per lijn toegevoegd.

## 8. Falsifiers

De envelopebranch faalt wanneer:

- er slechts één gebonden radius bestaat;
- de \(n\)-ladder alleen na handmatige quantisatie verschijnt;
- \(\ell,m,j\) niet ontstaan;
- de spectrumratio's niet convergeren;
- iedere lijn een eigen parameter vereist;
- selection rules niet volgen;
- de kern letterlijk tot atomaire schaal moet worden uitgerekt;
- de operator het bekende spectrum alleen reproduceert doordat de targetconstanten zijn ingevoerd.

## 9. Eerste verdedigbare target

Niet meteen de volledige Lamb shift, maar een parameterarme dimensieloze bound-state ratio:

\[
\boxed{
\mathcal R_{\rm env}
=
\frac{E_2-E_1}{E_3-E_1}
}
\]

voor één vooraf afgeleide operator, gevolgd door vergelijking met een onafhankelijke numerieke of experimentele benchmark.
