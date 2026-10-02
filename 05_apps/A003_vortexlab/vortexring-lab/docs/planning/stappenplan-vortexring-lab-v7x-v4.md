# Stappenplan vortexring-lab v7.x — versie 4 (na v7.4a)

**Stand:** v7.4a uitgeleverd op de v7.3.1-basis (jullie hotfix). Doorgestreept = uitgevoerd én geverifieerd (validator PASS + node-regressie groen op de actuele build). Niet doorgestreept = open werk, in aanbevolen volgorde.

**Versielijn tot nu toe:** v7 (wrijving) → v7.1 (B1–B8) → v7.2 (numerieke betrouwbaarheid + RP1–RP4) → v7.2.1 (jouw patch: ModelLog, aPhys-kiem) → v7.3 (dock, kernstraal, kleur, diag-hook) → v7.3.1 (jouw hotfix: ACN-TDZ, NaN-guards, ModelLog 0.2, contactvloer) → v7.4a (positionering, kleine helft).

---

## 0. Afgerond — ter referentie, niet meer plannen

~~**Fase 1 · v7.1 (B1–B8):** modusscheiding drift · tracertijd · Stewartson-ghost uit dynamica · Tw_proxy losgekoppeld · passieve diagnose · contact per RK4-stap · CFL over alle stages · redactie/BEL-byte.~~

~~**v7.1.1-restpunten (in v7.2):** tracers per CFL-stap · ghost uit ℓ_min/evalbudget (`dynamicFils`) · Γ_sheet/Γ_rel verwijderd, alleen dimensieloze q_S met getekende Ω · LIA-kruiswaarschuwing · booglengte-gewogen transport-proxy · hOm-correctie.~~

~~**Fase 2 · v7.2:** exacte segment-segmentafstand (Lumelsky/Ericson + prefilter, 6a-boogvenster) · first-hit-bisectie via puur `contactEvent()` · exacte polygonale Wr/Lk/ACN (Klenin–Langowski 1a; Hopf ±1 binnen 10⁻¹¹) · **trefoil-Wr gemeten 3.4180** (Fourier-verklaring bewezen, truncatie-hypothese weerlegd) · buis-gecorrigeerde wandmarges · zelftest T1–T6 met JSON-export.~~

~~**Gebruikspatch v7.2.1–v7.3:** OVERZICHT-dock · kernstraal zonder praktische ondergrens (vloer 1e-18 m) · vorticiteitskleur #0F1A29 · ModelLog (acties/stappen/events/diag) · parseLengthInput/fmtLengthSI/aPhys-readout (Fase-5-kiem).~~

~~**Hotfix v7.3.1 (extern):** ACN-TDZ · NaN-bestendige inputs · SI-parser am–m · coreFlowLock-ontgrendeling bij sub-n=1-radius · contactvloer max(3a, 64·ε·L_ref) · ModelLog 0.2 (drop-tellers, 5 Hz-diagcap, runtime-errorregistratie) · consistente provenance.~~

~~**Fase 3 kleine helft · v7.4a:** Ê_eff → geo-score Ŝ + γĤ-tekengevoeligheid gedocumenteerd · Rankine display-similarity-label · HUD χ_Ω · Ro · a/R · GP-constante als provenance-keuze (Roberts–Grant default, Track-B conditioneel) — audit-item 15 dicht · Γ_A·Γ_B-teken in botsing — audit-item 17 dicht · "achterwaarts integreren"-hernoeming.~~

---

## 1. Fase v7.4b — frames en meetlussluiting (VOLGENDE)

Het resterende, zwaardere deel van "wetenschappelijke positionering". Eén samenhangende refactorpatch:

1. **Frame-ontvlechting.** `P.coRot` stuurt nu zowel het solverframe als het displayframe én de achtergrondstroming. Splits in `P.solverFrame` ('lab'|'corot'), `P.displayFrame`, `P.bgFlow` — drie onafhankelijke keuzes. *Acceptatie:* frame-equivalentietest E_frame < 10⁻⁶ (zelfde fysische run in lab- en corot-solverframe, teruggetransformeerd, knooppuntsgewijs vergeleken) als zelftest-T8. Dit is het enige item waar v7.6-S architectureel op wacht (de bgOmegaCoupling-term in de wrijvings-v_n hangt eraan).
2. **ε_rev-uitlezing.** Round-tripfout bij achterwaarts integreren als HUD-waarde (machinerie bestaat al in zelftest-T5; naar runtime tillen met expliciete kostenwaarschuwing — een round-trip is 2× rekenwerk).
3. **g_a = d_min/a in de HUD**, via hergebruik van het 12-frame-stabiliteitsrapport (géén extra O(N²) per HUD-tick).
4. **Selftest-aanvulling:** T1-N-sweep (ringsnelheid bij N = 96/192/384, het laatste micro-gat uit Fase 2 §2.4).

## 2. Twee beslispunten — voor Omar, geen bouwwerk

5. **Stewartson-eindbesluit.** Optie A: dimensioneel gesloten afleiding met Ekman-getal E = ν/(ΩL²) — vergt een viscositeits- of HVBK-sluiting die met het inviscide model botst en eerlijk als aparte modeluitbreiding gelabeld moet worden. Optie B: definitief degraderen tot geometrische visualisatie (q_S-proxy blijft, alle kwantitatieve ambitie geschrapt). Tot de keuze valt blijft de v7.2-interimtoestand van kracht.
6. **coreFlowLock-default bij core='gp'.** Plan-advies: `false` (display-similarity hoort opt-in te zijn); kost: breekt de huidige SST-preset-ergonomie. Sinds v7.3.1 bestaat de expliciete ontgrendeling bij sub-n=1-radius al, wat de scherpste kant er af haalt.

## 3. Fase v7.5 — grote bouwstenen (elk een eigen ontwerpdocument vóór er code komt)

7. **Roterende continuumsolver** (∇·u = 0, Coriolis, drukprojectie, echte no-penetration op cilinder en bol) — de enige route naar een fysische Taylor-kolom/separatrix; het filamentlab kan dit principieel niet.
8. **Lokale GP-reconnectiebrug** (Koplik–Levine-route): filamentrun stopt bij d ≈ 4a → export (het ModelLog-Y-snapshotformaat is hiervoor het natuurlijke koppelvlak) → GP-doosje door de reconnectie → filamenten terugextraheren.
9. **Wandbeelden/BEM** voor de cilinder in het filamentmodel.
10. **Feynman-roostertest** (⟨ω_z⟩ = 2Ω, n_v = 2Ω/κ, b_△ ∝ Ω^(−1/2)) + vortex-wand-pinning — completeert audit-item 14 (v7's wrijving was de eerste helft).
11. **Axiale-gradiënt/lift-falsificatie** (SST-hypothese): fluxbalans per slab, tekenwissel bij gradiëntomkering, convergentie onder verfijning.

## 4. Fase v7.6-S — String/Rosetta-afronding

Kiem bestaat (parseLengthInput, fmtLengthSI, aPhys-readout, SI-invoer am–m uit v7.3.1). Nog te bouwen, ná v7.4b:

12. **S1-rest:** `L_PLANCK`-constante + presettabel — met `classicalE2` expliciet als **alias** van `sstCore` gelabeld (½r_e ≈ r_c is binnen SST een bewuste identificatie, geen tweede onafhankelijk ijkpunt) — en log-slider-mapping over de ~29 ordes.
13. **S2:** `runTheory`-runmodus (He-II | SST | String/Rosetta) + Rosetta-readoutkaarten (a/ℓ_P, a/r_c, R/a, log₁₀a; tension-proxy uitsluitend als readout, niet als energieclaim; α_ring-naamgevingsfirewall).
14. **S3 + guardrails (S7):** `radiusDrive`-schakelaar ('physical-only' default | 'simulation' expertmodus met waarschuwing) en numerieke Biot–Savart-vloer. **Dit sluit de bewuste planafwijking:** sinds v7.3 staat a < 1 µm al open in de dynamica zonder vangrail — verdedigbaar als expertmodus met ModelLog als compensatie, maar de schakelaar hoort er alsnog te komen.
15. **Zelftest-T7:** Planck-preset activeren laat de filamentdynamica bit-voor-bit ongewijzigd zolang `radiusDrive ≠ 'simulation'` (acceptatie-eis S8 + toevoeging uit plan v2).

## 5. Openstaande onderzoeksvraag (geen code, wel gate)

16. **a↔ξ-radiusconventiecheck** voor de GP-constante: is de a in U = Γ/(4πR)[ln(8R/a) − Δ] dezelfde ξ-definitie als in de Track-B-kern-ODE? Zolang dit openstaat blijft de Track-B-optie in het v7.4a-keuzepaneel terecht "conditioneel" gelabeld. Dit is een documenten-/afleidingscheck in het χ-fasepakket, geen simulatorwerk — maar wel de gate om dat label ooit te mogen verwijderen.

## 6. Uitvoeringstabel

| Fase | Inhoud | Omvang | Status |
|---|---|---|---|
| ~~v7.1~~ | ~~B1–B8~~ | — | ✔ afgerond, extern gereviewd |
| ~~v7.2~~ | ~~afstanden/bisectie, exacte Wr/Lk/ACN, wandmarge, zelftest~~ | — | ✔ afgerond, tests groen |
| ~~v7.2.1–v7.3.1~~ | ~~gebruikspatch + hotfix~~ | — | ✔ afgerond (deels extern) |
| ~~v7.4a~~ | ~~positionering, kleine helft~~ | — | ✔ afgerond deze sessie |
| **v7.4b** | frame-ontvlechting + E_frame-test, ε_rev, g_a, T1-sweep | middel (refactor) | **volgende** |
| beslispunten | Stewartson · coreFlowLock-default | — | wachten op Omar |
| v7.5 | continuumsolver, GP-brug, BEM, roostertest+pinning, lift | groot | per ontwerpdoc |
| v7.6-S | String/Rosetta S1-rest/S2/S3 + radiusDrive + T7 | middel | na v7.4b |
| gate | a↔ξ-conventiecheck (χ-fasepakket) | klein, buiten simulator | open |

**Rationale volgorde:** v7.4b eerst omdat de frame-ontvlechting het enige resterende architectuurwerk is waar v7.6-S op wacht, en omdat E_frame/ε_rev de laatste twee meetbare integriteitsclaims sluiten. De beslispunten kosten geen bouwtijd en kunnen parallel. v7.5-items pas na een ontwerpdocument per stuk — elk daarvan is groter dan alles wat tot nu toe in één patch is gedaan.
