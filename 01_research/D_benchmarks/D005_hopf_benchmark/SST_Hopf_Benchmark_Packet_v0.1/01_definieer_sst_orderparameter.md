# Stap 1 — Definieer eerst het SST-orderparameter

## Doel

Construeer een SST-specifiek complex dubbelveld

\[
\Phi(\mathbf x)=
\begin{pmatrix}\phi_1(\mathbf x)\\\phi_2(\mathbf x)\end{pmatrix}
\]

waaruit

\[
\Psi=\frac{\Phi}{\sqrt{\Phi^\dagger\Phi}},
\qquad
\mathbf n=\Psi^\dagger\boldsymbol\sigma\Psi
\]

worden afgeleid.

## Gatekoppeling

Primair: **H4**. Voorbereidend op H0–H3.

## Minimale voorwaarden

\[
\Phi^\dagger\Phi>0
\]

op het gehele domein,

\[
\mathbf n(\mathbf x)\to\mathbf n_\infty
\quad(|\mathbf x|\to\infty),
\]

en

\[
\Psi\sim e^{i\chi}\Psi
\]

moet dezelfde fysieke configuratie representeren.

## Eerste SST-ansatz

\[
\phi_1=A_1e^{i\theta_{\rm circ}},
\qquad
\phi_2=A_2e^{i\theta_{\rm frame}}.
\]

Mogelijke interpretatie:

- \(\theta_{\rm circ}\): circulatie-/Swirl-Clockfase;
- \(\theta_{\rm frame}\): framing-/twistfase;
- \(A_1,A_2\): amplitudes uit coreprofiel, vorticiteit of lokale modes.

Status: **[SST ANSATZ]** totdat dit uit de SST-actie volgt.

## Werkpakketten

1. Inventariseer \(\mathbf u,\boldsymbol\omega,\mathbf X(s)\), lokaal frame, coreprofiel, \(\Gamma\) en fasevelden.
2. Definieer dimensie, transformatiewet en nulpunten van \(\phi_1,\phi_2\).
3. Registreer alle punten met \(\Phi^\dagger\Phi\le\varepsilon_N\) als defect.
4. Scheid gemeenschappelijke gaugefase van fysische relatieve fase.
5. Construeer een vaste randwaarde voor \(\mathbf n\).
6. Test frame- en parametrisatie-onafhankelijkheid.

## Tests

- \(\min\Phi^\dagger\Phi>\varepsilon_N\);
- \(\Delta_{\rm norm,\Psi}<\varepsilon_\Psi\);
- \(\Delta_{\rm norm,n}<\varepsilon_n\);
- gaugeverandering laat \(\mathbf n\) invariant;
- randwaarde convergeert;
- gridverfijning verandert de topologische sector niet.

## H4 passcriterium

Een orderparameter krijgt alleen `PASS` wanneer hij glad, nergens nul, randcompactificeerbaar en reproduceerbaar is.

## Output

- `sst_order_parameter.json`;
- spinor- en directorveld;
- defectledger;
- gaugeconventie;
- H4-evidence.

## Niet claimen

- dat \(\Psi\) al een quantumtoestand is;
- dat de twee componenten spin-up/down zijn;
- dat de gaugefase reeds elektromagnetische \(U(1)\) is.
