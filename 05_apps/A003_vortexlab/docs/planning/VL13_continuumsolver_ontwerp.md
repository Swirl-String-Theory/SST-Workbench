# VL13 — Roterende continuumsolver / Fluid-P3 (ontwerp)

**Status:** ontwerpdoc klaar · wacht op ACK · geen code  
**Parent-plan:** [`.cursor/plans/vortexlab_v7x/VL13_continuumsolver.plan.md`](../../../../.cursor/plans/vortexlab_v7x/VL13_continuumsolver.plan.md)  
**Voorkeurvolgorde:** na VL12; eigen major research track  
**Bron:** Stappenplan v6 §5 v7.5.4 · v4/v5 §3 item 7 · Fluid-P2 (pressure Poisson / cylindrical impermeability / Euler closure UNRESOLVED)

---

## 1. Hypothese / doel

**Doel.** Een roterende incompressibele continuumsolver (\(\nabla\cdot u=0\), Coriolis, drukprojectie, echte no-penetration op cilinder en bol/caps) — de **enige** route naar een fysisch gesloten Taylor-kolom/separatrix in VortexLab. Dit dekt Fluid-P3.

**Hypothese H13.** Op gedocumenteerde ankerstromingen (Taylor–Couette-achtig / kolom) convergeert de solver naar referentieoplossingen binnen vooraf vastgelegde fouten, met pressure-Neumann-compatibiliteit en vorticity-curl / invariant-parity checks — zonder filament-proxy als valse continuum-PASS.

**Wat al bestaat.** Filamentlab + bgFlow wall/bundle; diagnostische \(\nabla\cdot u\)-samples en wall \(|u\cdot n|\); tube-BEM; cilinder-BEM gepland (VL11). Filamentlab kan Taylor-kolom/separatrix **principieel niet** fysisch sluiten.

---

## 2. Observabelen

| ID | Observabele | Rol |
|----|-------------|-----|
| O1 | \(\|\nabla\cdot u\|\) (grid) | Incompressibiliteitsresidu na projectie |
| O2 | \(\max\|u\cdot n\|\) wand/caps | No-penetration residual |
| O3 | Druk Poisson residual / Neumann-compatibiliteit | Fluid-P3 eis |
| O4 | Coriolis / rotatieparameter \(\Omega\) | SI, in config |
| O5 | Ankerfouten vs referentie | L2/L∞ op \(u\) (en desgewenst \(p\)) |
| O6 | CFL / dt | Geen stille ondervloer; stop bij onveilige dt |
| O7 | Vorticity-curl / invariant parity | P3-paritygates |
| O8 | Provenance | Engine-versie, gridhash, units, seed |

---

## 3. Falsificatie- / acceptatiecriteria (vóór runs)

1. **Ankerstromingen.** Minstens één Taylor–Couette-achtig en één kolomachtig anker met gedocumenteerde foutgrenzen \(\varepsilon_u\) (vast vóór productieclaims).
2. **Projectie.** Na drukprojectie: \(\|\nabla\cdot u\| < \varepsilon_{\rm div}\) op het rekengrid.
3. **No-penetration.** \(\max|u\cdot n| < \varepsilon_n\) op wand en caps (continuum-BC, niet filament-BEM-proxy).
4. **Geen filament-PASS-as-continuum.** Filamentlab-diagnostics mogen niet als Fluid-P3 PASS worden geëxporteerd; aparte statusnamespace (`continuumQualification` ≠ `fluidQualification` filament-P2).
5. **P2→P3 promotie alleen met bewijs.** Bestaande UNRESOLVED-labels verdwijnen uitsluitend na groene P3-gates + onafhankelijke Euler-referentie waar vereist.
6. **SI + CFL.** Alle velden SI; CFL-schending → stop/FAIL, geen stille `max(dt_floor)`.

**Interpretatie:** PASS = continuum-BC en projectie overleven ankers; **niet** automatische bevestiging van SST-speculatieve klokwetten.

---

## 4. Eerlijkheidsgrenzen

- Filament + BEM blijven vergelijkings-/inbeddingslaag, geen vervanging van continuum.
- Low-Re / ideële Euler-keuze moet expliciet in config; viscositeit niet stilzwijgend «aan».
- Gridresolutie en domein Truncatie zijn eerste-orde foutbronnen; rapporteren, niet verbergen.
- Native/worker-pad waarschijnlijk nodig; monoliet-HTML is geen acceptabele enige host voor P3.
- Swirl-Clock canonieke wet (VL07) blijft buiten deze solverclaim.

---

## 5. Koppelvlak met bestaande runtime

| Component | Rol in VL13 |
|-----------|-------------|
| **Filamentlab** | Blijft beschikbaar; mag velocity/druk van continuum **inlezen** als bgFlow-achtige laag na expliciete bridge, nooit omgekeerd stilzwijgend |
| **BEM (tube / VL11 cilinder)** | Validatievergelijking en overgangspad; continuum vervangt BEM niet automatisch in UI |
| **ModelLog** | Logt continuum-engine id/versie, gridhash, O1–O7, aparte qualification-blok |
| **EngineClient / SSTcore-adapter** | Voorziene IPC: browser ↔ native/worker (zie `SSTCORE_NODE_PLAN.md` / ARCHITECTURE); protocol in implementatiefase bevriezen |
| **Fluid-P2 tests** | `npm run check` blijft filament-P2 dekken tot integratie; continuum krijgt **apart** testpakket |

**Architectuurvoorstel (vast te leggen bij ACK):** apart package of workerproces; deterministische replay via ModelLog-Y of continuum-checkpointschema; geen vermenging van RESEARCH-filamentgates met continuum-PASS.

---

## 6. Tests

| Fase | Test |
|------|------|
| Nu | Geen runtimewijziging |
| Na ACK | Apart continuum-testpakket (ankers, div, wall, CFL-stop) |
| Integratie later | Contracttests EngineClient; filament-P2 regressie blijft groen |
| Verboden | «PASS» op filament-proxy alsof continuum gesloten is |

---

## 7. Buiten scope

- GP-reconnectiebrug (VL14) — tenzij later hergebruikt als hostveld
- Canonieke SST-klokwet / confirmatory VL07
- M2-modularisatie van `vortexlab-runtime.js` (epic buiten scope)
- Productie-campagne volle resolutie zonder apart verzoek

---

## 8. ACK-checklist (Omar)

- [ ] Continuum is erkend als enige route naar fysische Taylor-kolom/separatrix.
- [ ] Ankers + \(\varepsilon\)-drempels worden vóór claims vastgezet.
- [ ] Aparte qualification-namespace t.o.v. filament-P2 is akkoord.
- [ ] Native/worker (niet monoliet-only) is akkoord als default architectuur.
- [ ] Koppelvlak ModelLog + EngineClient/SSTcore is richtinggevend akkoord.
- [ ] **ACK:** implementatie mag starten · **NACK:** herzien ontwerp (geen code).

**ACK-ruimte:** datum / paraaf Omar: _______________
