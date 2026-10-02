# Stappenplan vortexring-lab v7.x — versie 6 · route naar v7.5

**Stand:** twee parallelle sporen op de v7.4-basis: **v7.4.1** (auditcorrectie; geverifieerd: syntax groen, provenance/geo-diagnostiek/capaciteitsscheiding aanwezig, géén bundelcode) en **SST-vortexbundel r1** (40 KB-diff óp v7.4, niet op v7.4.1). Ze zijn nog niet samengevoegd — dat is de eerste stap hieronder.

**Verificatie configuratieverslag (nagerekend, niet aangenomen):** Ω_core = Γ₀/(2πr_c²) = 7.76344×10²⁰ s⁻¹ ✓ · n_v(Ω=1) = 2Ω/Γ₀ = 2.06534×10⁸ m⁻² ✓ · N_phys = n_vπR_b² ≈ 2.1023×10⁷ ✓ · de splay-kinematica klopt: uit ω = −rΩ′r̂ + 2Ωẑ volgt dr/dz = −(r/2)d lnΩ/dz en dus r√|Ω| = const, exact consistent met λ↔Ω∝λ⁻². De eerlijkheidsgrenzen in het verslag zijn correct gesteld: representatieve sampling (61 lijnen ≠ 10⁷ kernlijnen), kinematische ansatz ≠ drukgesloten oplossing, α=α′=0 want SST-canon heeft geen wrijvingswaarde, wand blijft volume-only tot BEM.

---

## 0. Afgerond (samengevat; detail in plan v5)

~~v7.1 (B1–B8) · v7.1.1-restpunten · v7.2 (exacte afstanden/bisectie, exacte Wr/Lk/ACN, trefoil-Wr 3.4180, wandmarges, zelftest) · v7.2.1–v7.3 (dock, kernstraal, ModelLog) · v7.3.1-hotfix · v7.4a (positionering klein) · v7.4.1 (provenance, pseudo-energie eruit, |χ_Ω|/Ro_z-guards, s_A·s_B, GP-Δ in MODEL→KERN, capaciteit paars/los van stabiliteit, T0e–h).~~

## 1. Kritische punten op de bundel-branch — vóór de merge afhandelen

1. **Dubbeltellingsrisico Ω_wall × Ω_bundle.** De legacy `bgOmegaCoupling`-term (Ω×r in lab-frame) en het nieuwe opgelegde veld u_bundle = Ω_bundle(z)ẑ×r zijn beide achtergrond-superflow-bijdragen in `velocityCore`. Als beide tegelijk actief kunnen zijn superponeren ze stilzwijgend. Eis: wederzijdse exclusiviteit afdwingen in code (niet alleen in de preset), met een flag als beide aan staan. Het verslag legt de preset goed vast (Ω_wall = 0, legacy-koppeling uit) maar een preset is geen invariant.
2. **Wrijving × bundel ongedefinieerd.** Bij α≠0 hoort u_bundle in v_s van de Schwarz-term, maar wat is dan v_n? Co-roterend met de bundel, met de wand, of uniform? Tot daar een keuze ligt: T>0 hard blokkeren zodra de bundelveldkoppeling aan staat (de baseline zet α=0, maar ook hier: afdwingen, niet aannemen).
3. **Ω_core read-only is de juiste firewall** — 10²⁰ s⁻¹ in welke dynamische koppeling dan ook zou de CFL vernietigen. Acceptatietest: geen enkel codepad muteert P vanuit Ω_core.
4. **Splay + periodieke z:** het verslag schakelt periodieke grens terecht uit bij monotone splay; check dat `wrapFilamentCarriersZ` en `tracerWrapZ` dat allebei respecteren, niet alleen de UI.

## 2. Fase v7.4.2 — reconciliatie-merge (EERSTE STAP, blokkerend)

Eén canonieke trunk maken: **bundle-r1 rebased op v7.4.1** (niet andersom — de auditcorrecties raken labels/HUD/validator die de bundel-diff niet kent). Inhoud:

1. Merge + conflictresolutie (verwachte botsingen: HUD-rijen, MODEL-paneelindeling, ModelLog-schema, zelftestnummering).
2. Exclusiviteitsguards uit §1.1–1.2 inbouwen.
3. **Bundeltests uit verslag §7 als zelftests T9a–e:** fluxbehoud ε_Φ < 10⁻¹² (analytische generator) · wandonafhankelijkheid (identiek traject bij verschillende Ω_wall, koppeling uit) · rendering-onafhankelijkheid (31/61/121 lijnen bit-identiek) · tekeninversie (Ω_bundle→−Ω_bundle: richting keert, n_v en N_phys invariant, geen antivortices) · splay-waarschuwing (veldkoppeling automatisch uit bij profielwissel).
4. Validator-v7.4.2 die beide markersets (audit + bundel) eist.
*Acceptatie:* validator PASS, alle T0–T9 groen, node-regressie groen.

## 3. Fase v7.4b — frames (verkleind door de bundel-branch)

De Ω-drieluik (Ω_core/Ω_bundle/Ω_wall) van de branch dekt de "rol-splitsing" van het oude plan-item al. Wat rest: `P.solverFrame`/`P.displayFrame`/`P.bgFlow` als onafhankelijke keuzes (P.coRot stuurt nu nog solver én display), met **E_frame < 10⁻⁶ als zelftest-T8** — merk op dat de wandonafhankelijkheidstest T9b hier al een halve E_frame-test is. Plus: ε_rev-HUD, g_a = d_min/a via het 12-frame-rapport, T1-N-sweep.

## 4. Beslispunten (ongewijzigd, voor Omar)

Stewartson-eindbesluit (Ekman-sluiting of definitief visueel) · coreFlowLock-default bij gp — **let op:** de bundel-baseline eist al `coreFlowLock=false` voor de SST-preset; daarmee is de helft van dit beslispunt de facto genomen en resteert alleen de default buiten de preset.

## 5. Fase v7.5 — grote bouwstenen, herordend op wat de bundel mogelijk maakt

De bundel-branch verandert de natuurlijke volgorde: twee van de vijf blokken hebben er nu een fundament.

**v7.5.1 · Lift-falsificatie op de bundel (eerst — het fundament ligt er).** De splay-machinerie ís de fluxbalans-per-slab uit het oude item 11. Ontwerpkader: (a) hypothese expliciet als SST-claim formuleren (axiale gradiënt in bundeldichtheid ↔ lift/impulsflux, tekenwissel bij gradiëntomkering); (b) observabelen: impulsflux per z-slab uit het coarse-grained veld + filamentrespons van een testring in de bundel; (c) falsificatiecriteria vóóraf: tekenwissel onder λ-omkering, convergentie onder lijnverfijning (T9c garandeert al rendering-onafhankelijkheid), en nul-effect bij parallel profiel als controle; (d) eerlijkheidsgrens: zolang splay geen drukgesloten oplossing is, is elk resultaat conditioneel op de kinematische ansatz — dat hoort in elke uitvoer-JSON als caveat-veld.

**v7.5.2 · Wandbeelden/BEM.** Nodig om "passieve cilinder" (Ω_wall = 0, volume-only) te upgraden naar echte u·n = 0 — het verslag benoemt dit zelf als ontbrekend (§6.3). Eigen ontwerpdoc.

**v7.5.3 · Feynman-rooster-completion + pinning.** De bundel is de coarse-grained helft van item 10; wat rest is de discrete kant (⟨ω_z⟩ = 2Ω-check tegen het samplingveld, b_△ ∝ Ω^(−1/2), Tkachenko/defecten expliciet buiten scope per §6.2) en vortex-wand-pinning (sluit audit-item 14 definitief).

**v7.5.4 · Roterende continuumsolver.** Ongewijzigd het grootste blok; pas na 5.1–5.3, en de enige route naar een fysische Taylor-kolom/separatrix.

**v7.5.5 · GP-reconnectiebrug.** ModelLog-Y-snapshots als koppelvlak (ongewijzigd).

## 6. Fase v7.6-S en de gate (ongewijzigd)

String/Rosetta S1-rest/S2/S3 + radiusDrive-guardrails + zelftest-T7 — **noot:** de bundel-branch gebruikt a_phys = r_c al als aparte grootheid naast a_sim (verslag §4, MODEL→KERN); daarmee is de aSim/aPhys-splitsing feitelijk in productie en wordt v7.6-S vooral UI/guardrail-afronding. De a↔ξ-conventiecheck blijft de gate voor het Track-B-Δ-label.

## 7. Uitvoeringstabel

| Fase | Inhoud | Status |
|---|---|---|
| ~~t/m v7.4.1~~ | ~~zie plan v5~~ | ✔ afgerond |
| **v7.4.2** | merge v7.4.1 ⊕ bundel-r1 + exclusiviteitsguards + T9a–e + validator | **volgende, blokkerend** |
| v7.4b | solver/display/bgFlow-splitsing + T8, ε_rev, g_a, T1-sweep | na merge (verkleind) |
| beslispunten | Stewartson · coreFlowLock-default (half genomen via bundel-baseline) | Omar |
| v7.5.1 | lift-falsificatie op de bundel (ontwerpkader in §5) | eerst van v7.5 |
| v7.5.2–5 | BEM · rooster+pinning · continuumsolver · GP-brug | per ontwerpdoc |
| v7.6-S | Rosetta-afronding (aPhys al in productie) + gate a↔ξ | na v7.4b |

**Rationale:** de merge eerst, want twee divergerende trunks op v7.4 is de snelste route naar onvindbare regressies; daarna is v7.5.1 de goedkoopste wetenschappelijke opbrengst omdat de bundel-branch er 80% van het gereedschap voor heeft neergezet — mits de falsificatiecriteria vóór de eerste run vastliggen, niet erna.
