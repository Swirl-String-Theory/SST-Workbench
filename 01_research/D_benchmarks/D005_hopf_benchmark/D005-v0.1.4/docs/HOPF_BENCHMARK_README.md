# SST Hopf Benchmark Packet v0.1

## Doel

Dit pakket operationaliseert de route

\[
\text{SST-orderparameter}\rightarrow\text{Hopf-map}\rightarrow Q_H
\rightarrow\mathcal H\rightarrow\text{spinbundel}\rightarrow s=\tfrac12.
\]

De route is geen voltooide elektronafleiding. Iedere stap draagt een status:
`ORTHODOX`, `BRIDGE`, `SST_ANSATZ` of `OPEN_THEOREM_TARGET`.

## Acht stappen

1. `01_definieer_sst_orderparameter.md`
2. `02_analytische_hopf_benchmark.md`
3. `03_toroflux_spinorveld.md`
4. `04_hopf_lading_numeriek.md`
5. `05_heliciteitsbridge.md`
6. `06_effectieve_spinactie.md`
7. `07_vier_pi_configuratieruimte.md`
8. `08_trefoil_integratie.md`

## H0–H10 gates

| Gate | Naam | Centrale test | Passconditie | Stap |
|---|---|---|---|---|
| **H0** | Analytische Hopf-map | Correcte normalisatie van \(\Psi,\mathbf n\) | \(\Psi^\dagger\Psi=1\), \(|\mathbf n|=1\) binnen tolerantie | 2 |
| **H1** | Hopf-lading | Integerconvergentie | \(Q_H\to\pm1\) voor benchmark onder gridverfijning | 2, 4 |
| **H2** | Gauge-invariantie | \(\Psi\mapsto e^{i\chi}\Psi\) | \(Q_H\) invariant binnen \(\varepsilon_{\rm gauge}\) | 2, 4 |
| **H3** | Preimage-linking | Integraal versus inversebeeldlinking | \(Lk=Q_H\) binnen foutbudget | 2, 4 |
| **H4** | Toroflux-mapping | Glad, nergens nul SST-orderparameter | \(\Phi^\dagger\Phi>0\), vaste randwaarde, reproduceerbare mapping | 1, 3 |
| **H5** | Helicity bridge | SST-vorticiteit versus Hopf-kromming | Kleine \(\Delta_\omega,\Delta_{\mathcal H}\) | 5 |
| **H6** | Gereduceerde actie | Berryterm uit SST-dynamica | Afgeleide \(\kappa_B\), niet ingevoerd | 6 |
| **H7** | Bundelquantisatie | Integrale symplectische flux | \(\kappa_B/\hbar\in\mathbb Z\) | 6 |
| **H8** | Spinselectie | Waarom elektronsector \(k=1\) kiest | Dynamische/topologische selectieregel | 6 |
| **H9** | \(4\pi\)-configuratieruimte | Niet-triviale \(2\pi\)-lus | \(\mathbb Z_2\)-guard of equivalent FR-resultaat | 7 |
| **H10** | Trefoil-integratie | Onafhankelijke certificatie van \(K\) en \(Q_H\) | Stabiele \((K,Q_H)\)-classificatie en eventledger | 8 |

## Afhankelijkheden

```text
H4 ─► H0 ─► H1 ─► H2 ─► H3 ─► H5 ─► H6 ─► H7 ─► H8
                                      └────────────► H9
H0–H9 ─────────────────────────────────────────────► H10
```

## Centrale formules

\[
\Psi^\dagger\Psi=1,\qquad
\mathbf n=\Psi^\dagger\boldsymbol\sigma\Psi,
\]

\[
a=-i\Psi^\dagger d\Psi,\qquad f=da,
\]

\[
Q_H=\frac{1}{4\pi^2}\int a\wedge f
=\frac{1}{4\pi^2}\int\mathbf a\cdot\mathbf b\,d^3x,
\]

\[
\mathbf u_H=\frac{\Gamma}{2\pi}\mathbf a
\quad\Longrightarrow\quad
\mathcal H_H=\Gamma^2Q_H,
\]

\[
\Omega_s=2s\hbar f,\qquad
\frac{1}{2\pi\hbar}\int_{S^2}\Omega_s=2s\,c_1\in\mathbb Z.
\]

Voor \(c_1=1\) en de minimale niet-triviale sector volgt \(s=\tfrac12\), maar de selectie van die sector blijft H8.

## Gemeenschappelijke residuals

\[
\Delta_{\rm norm,\Psi}=\|\Psi^\dagger\Psi-1\|_\infty,
\]

\[
\Delta_{\rm norm,n}=\||\mathbf n|^2-1\|_\infty,
\]

\[
\Delta_{\rm div}=
\frac{\|\nabla\cdot\mathbf b\|_2}{\|\mathbf b\|_2+\epsilon},
\qquad
\Delta_{\rm curl}=
\frac{\|\nabla\times\mathbf a-\mathbf b\|_2}{\|\mathbf b\|_2+\epsilon},
\]

\[
\Delta_{\rm int}=|Q_H-\operatorname{round}Q_H|,
\]

\[
\Delta_{\mathcal H}=
\frac{|\mathcal H_{\rm SST}-\Gamma^2Q_H|}
{|\mathcal H_{\rm SST}|+\Gamma^2|Q_H|+\epsilon}.
\]

## Verplichte evidence per gate

Iedere gate-output bevat minimaal:

```json
{
  "gate": "H1",
  "status": "PASS | FAIL | INDETERMINATE",
  "epistemic_class": "ORTHODOX | BRIDGE | SST_ANSATZ | OPEN_THEOREM_TARGET",
  "parameters": {},
  "residuals": {},
  "input_sha256": "...",
  "software_version": "...",
  "commit": "..."
}
```

## Niet toegestaan

Dit pakket rechtvaardigt nog niet:

- \(Q_H=e\);
- \(K=3_1\Rightarrow Q_H=1\);
- de numerieke waarde van \(\hbar\);
- de Diracvergelijking;
- \(g=2\);
- fermionische statistiek zonder H9;
- een volledige elektronafleiding zonder H4–H10.
