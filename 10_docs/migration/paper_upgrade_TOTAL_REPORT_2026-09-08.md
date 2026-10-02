# Totaalrapport — Paper-upgrade epic (2026-09-08)

**Kort:** engineering-integratie PU00–PU04 is groen. De nieuwe paper-gates (2505 / 1806) zijn **nog niet** als wetenschappelijke production gates uitgevoerd. PU05–PU08 blijven terecht gepauzeerd — niet omdat SST al is gefalsificeerd, maar door numerieke invaliditeit (A037), een echte oude QHP-FAIL (A034), en ontbrekende production certificates.

Index: [README.md](README.md) · Corrected framing: 2026-09-08 (v2)

---

## 0. Gecorrigeerde statuslabels

\[
\boxed{
\begin{aligned}
A037 &: \texttt{INVALID\_NUMERICS / NOT\_YET\_TESTED\_2505}\\
A034 &: \texttt{OLD\_QHP\_DYNAMIC\_GATE\_FAIL / NOT\_YET\_TESTED\_1806}
\end{aligned}}
\]

| Family | Engineering | Oude science | Nieuwe paper gate | Promotion |
|--------|-------------|--------------|-------------------|-----------|
| **D006** | PASS | harness `NOT_FALSIFIED` (synthetic) | n.v.t. | infra OK |
| **C006** | PASS | quick PASS/diagnostic; K6=SKIP | gedeeltelijk | infra OK |
| **A037** | PASS | **INVALID_NUMERICS** (6/6 timestep) | **NOT RUN** (2505) | ❌ |
| **A034** | PASS | **FAIL_NO_RESTORING_STRUCTURE** | **NOT RUN** (1806) | ❌ |
| **A029+** | — | — | blocked | ❌ |

---

## 1. Subplan-overzicht

| ID | Wat | Status | Uitkomst |
|----|-----|--------|----------|
| **PU00–PU01b** | Selftests, hooks, resume/heartbeat | DONE | **PASS** |
| **PU02** | Certificate pipeline (synthetic) | DONE | Pipeline PASS; **unsafe PASS labels** |
| **PU03** | D006 + C006 | DONE | Infra PASS |
| **PU04** | A037 → A034 basic campaigns | DONE | Eng. PASS; science as §0 |
| **PU02b** | Certificate semantics / no synthetic promotion | DONE | Synthetic ≠ promotable; consumers reject |
| **PU04b–d** | A037 numerics → 2505; A034 dual branch | PLANNED | After PU02b |
| **PU05–PU08** | Downstream | BLOCKED | Correct pause |

---

## 2. Infrastructuur is groen ✅

Niet opnieuw aan besteden:

- 18/18 paper-upgrade selftests; `run_paper_upgrade` in run-chains; resume/heartbeat
- D006 + C006 native (na `py::ssize_t`); A037/A034 lopen technisch door; blind/reveal OK

### D006

`NOT_FALSIFIED` = **harness-certificatie** op synthetische calibration/geometry.
\(\chi_\nu^2\sim 2.35\times10^{-26}\) is geen nieuw fysisch SST-resultaat.

### C006

Infra groen. \(K6=\texttt{SKIP}\) ⇒ geen accepted RPO ⇒ geen true Floquet-resultaat (correct).

---

## 3. A037 — nog geen SST-falsificatie

Alle zes pairs: `INVALID_TRAJECTORY_TIMESTEP` ⇒

\[
\boxed{\text{observable mag wetenschappelijk niet beoordeeld worden}}
\]

niet “symmetry-selection hypothesis failed.”

| Pair | max CFL | max \(\|\Delta L\|\) | max \(ds\)-CV |
|------|--------:|---------------------:|--------------:|
| P0001 | 3.21 | 2.12 | 0.987 |
| P0002 | 4.97 | 5.47 | 0.703 |
| P0003 | 2.52 | 4.20 | 0.795 |
| P0004 | 3.01 | 0.033 | 0.595 |
| P0005 | **10.25** | 2.95 | 0.708 |
| P0006 | **10.53** | 6.98 | 0.750 |

\[
\boxed{\text{N=72 basic trajectory is numeriek onvoldoende opgelost.}}
\]

### Mirror algebra (code sanity, niet physical detection)

P0001: \(\Pi_A\approx+0.1547879\), \(\Pi_B\approx-0.1547879\), odd residual \(\sim1.4\times10^{-14}\).
Door de set: \(\Xi_H[PK]\simeq-\Xi_H[K]\), \(\Pi[PK]\simeq-\Pi[K]\); excitation residuals \(\sim10^{-13}\)–\(10^{-11}\).

P0005: \(\mathrm{CFL}_{\max}\approx10.25\) maar \(\epsilon_{\Pi,\mathrm{odd}}\approx9.8\times10^{-16}\).

\[
\boxed{\text{mirror covariance van de code} \neq \text{gekwalificeerde fysieke transportrespons}}
\]

### Paper-2505 nog niet uitgevoerd

Directory `A037-v0.3.0` runt nog v0.2.0 chain (`SST-CHIRALITY-ANALYSIS-2.0`).
Geen \(\chi_{ij}\), \(\chi^A\), orientation sweeps, forbidden residuals, rotation-covariance.
Alleen `paper_upgrade/gate.py --selftest` + synthetic cert.

---

## 4. A034 — echt negatief voor oude QHP-dynamic gate

588 candidates → 33 zero crossings → **0** confirmed restoring / fixed points / affine FPs.

\[
\boxed{\text{op deze sampled QHP manifold is geen gekwalificeerd restoring point gevonden.}}
\]

### Trefoil \(3_1\)

- \(f_{\mathrm{proj}}\approx0.00255\), short \(\approx0.0192\) vs gate \(\ge0.05\) → veel beweging **buiten** QHP-manifold
- \(\lambda(J)\approx\{-0.1118,\;0.00920,\;0.000475\}\) (twee positieve)
- short: \(\approx\{-0.1099,\;0.0275,\;-0.000464\}\) → **saddle / non-restoring**

### Paper-1806 nog niet uitgevoerd

Package `0.1.3` / formats `SST-QHP-*-1.3` = \(\mathbf F,J\) methode.
Constrained \(g_{\mathcal M}, H_{\mathcal M}\) inputs bestaan niet als campaign-output ([PU02_GAPS.md](PU02_GAPS.md)).

Bewaar `DYNAMIC_QHP_RESTORING = FAIL`; voeg later onafhankelijk `CONSTRAINED_ENERGY_ADMISSIBILITY = ?` toe ([PU04d](PU04d_a034_dual_branch.plan.md)).

---

## 5. Certificates — niet downstream gebruiken ⚠️

Huidige on-disk certs hadden `status: PASS` / `ENERGETICALLY_ADMISSIBLE` uit **synthetic** selftest-data.

Consumerregel (PU02b):

\[
\boxed{
\texttt{promotion\_allowed}
=
(\texttt{scientific}=\texttt{true})
\land
(\texttt{certificate\_kind}=\texttt{CAMPAIGN})
\land
(\texttt{status}\in\{\texttt{PASS},\texttt{QUALIFIED}\})
}
\]

---

## 6. Volgende volgorde — production-certification patchset

**Geen nieuwe physics.** Zie [PRODUCTION_CERTIFICATION.plan.md](PRODUCTION_CERTIFICATION.plan.md).

\[
\boxed{
\text{PC00 Certificate Hardening}
\rightarrow
\text{A037 v0.3.1}
\rightarrow
\text{A034 v0.2.1}
\rightarrow
\text{A038 v0.4.1}
}
\]

(+ D006 **v0.4.1** regressions; tip is v0.4.0 niet v0.3.0)

| Patch | Doel |
|-------|------|
| [PC00](PC00_certificate_contract.plan.md) | `SST-SCIENTIFIC-CERTIFICATE-1.0` + `promotable()` |
| [PC01](PC01_d006_regression.plan.md) | parity+CFL / fake selftest / weak manifold |
| [PC02](PC02_a037_v031.plan.md) | qual ladder + χ_ij; mirror ≠ physical response |
| [PC03](PC03_a034_v021.plan.md) | keep dynamic FAIL + energy branch + richer labels |
| [PC04](PC04_a038_v041.plan.md) | firewall; `BLOCKED_UPSTREAM_*` ≠ `FAIL_TREFOIL` |

Daarna pas opnieuw: `D006 → A037 → A034 → A038 preflight`, en alleen bij promotable certs de modal/Floquet-keten.

---

## 7. Onderzoeksresultaten uit deze incomplete run

1. **A037:** mirror/parity blijft extreem consistent terwijl integratie faalt → aparte **code-certification** gate; niet als physical detection.
2. **A034:** geen dynamisch restoring FP op trefoil; klein deel van beweging in \((Q,H,P)\) → steun voor “laat dynamica DOFs kiezen” i.p.v. handgekozen shape family.
