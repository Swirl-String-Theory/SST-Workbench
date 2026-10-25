# VL14 — GP-reconnectiebrug (ontwerp)

**Status:** ontwerpdoc klaar · wacht op ACK · geen code  
**Parent-plan:** [`.cursor/plans/vortexlab_v7x/VL14_GP_reconnectiebrug.plan.md`](../../../../.cursor/plans/vortexlab_v7x/VL14_GP_reconnectiebrug.plan.md)  
**Voorkeurvolgorde:** na VL13, of parallel als GP-stack los staat  
**Bron:** Stappenplan v6 §5 v7.5.5 · v4/v5 §3 item 8  
**Referentie-route:** Koplik–Levine (lokale Gross–Pitaevskii reconnectie)

---

## 1. Hypothese / doel

**Doel.** Een gecontroleerde brug: filamentrun stopt bij kernafstand \(d \approx 4a\) → export → lokaal GP-doosje door reconnectie → filamenten terugextraheren → optioneel hervatten in het filamentlab.

**Hypothese H14.** Op een gecontroleerd anti-parallel vortexpaar met bekende topologieverandering levert de round-trip (filament → GP → filament) de verwachte reconnectie-topologie, met provenance (GP-engine versie + hashes), zonder stille tunneling wanneer extractie faalt.

**Wat al bestaat.** ModelLog + Y-snapshots; contactvloer \(\max(3a,\,64\cdot\varepsilon\cdot L_{\rm ref})\); topology guard met first-hit bisectie; runtime messaging dat reconnectie **niet** gemodelleerd is. Ontbreekt: GP-brug en numerieke reconnectie-acceptatie.

---

## 2. Observabelen

| ID | Observabele | Definitie (ontwerp) |
|----|-------------|---------------------|
| O1 | Stopafstand \(d\) | Minimale kern-kern (of centreline) afstand bij brugtrigger; doel \(\approx 4a\) (met \(a = a_{\rm sim}\) of expliciet gekozen schaal — bron gelogd) |
| O2 | \(a_{\rm sim}\) vs healing length \(\xi_{\rm GP}\) | Eenhedenmapping filament ↔ GP-doosje |
| O3 | Topologie vóór/na | Crossing/linking of paar-connectiviteit; verwacht verschil op ankerpaar |
| O4 | Extractiekwaliteit | Residual/fitfout bij filamentterugwinning uit GP-fase/dichtheid |
| O5 | GP-engine provenance | Versie, build-id, input/output hashes |
| O6 | Topology-guard status | Aan buiten brugvenster; gedrag binnen venster expliciet gelogd |
| O7 | Hervatingsvlag | Of filamentrun na extractie mag doorgaan |

---

## 3. Falsificatie- / acceptatiecriteria (vóór runs)

1. **Round-trip anker.** Anti-parallel paar met bekende topology change: na brug is O3 gelijk aan de vooraf gedocumenteerde verwachting (niet post-hoc).
2. **Stop bij \(d\approx 4a\).** Trigger venster gedocumenteerd (bijv. \(d/a \in [3.5,\,4.5]\) of first-hit op \(4a\)); buiten venster geen GP-aanroep.
3. **Mislukte extractie → FAIL.** Geen stille continue tunneling in filamentmodus; run stopt of markeert `reconnectBridge=FAILED_EXTRACT`.
4. **Topology guard default aan** buiten brugvenster; uitschakelen alleen met expliciete user/RESEARCH-vlag en ModelLog-event.
5. **Provenance verplicht.** Elke hervatting zonder GP-versie + hashes = FAIL van documentatiegate.
6. **Geen reconnectie op defaultpad.** Regressie: zonder brug-aanroep blijft messaging/gedrag «geen numerieke reconnectie».

**Interpretatie:** PASS = gecontroleerde Koplik–Levine-brug op ankerpaar; **niet** algemene SST-reconnectiewet en **niet** canonieke klokclaim.

---

## 4. Eerlijkheidsgrenzen

- Browserfilament blijft **free-filament** tot de brug expliciet wordt aangeroepen.
- \(a_{\rm sim}\) is numerieke kernschaal; niet stilzwijgend gelijkstellen aan fysische healing length zonder mappingtabel.
- Contactvloer en Float64-representatie (Fluid-P2) blijven relevant: sub-precisie cores mogen brug niet claimen als fysisch opgelost.
- GP-doosje is lokaal; verre filamentstructuur is bevroren/geëxtrapoleerd — foutbron rapporteren.
- Mislukte fase-unwrapping / extractie is eerste-klas falen, geen «bijna-reconnectie».

---

## 5. Koppelvlak met bestaande runtime

| Component | Rol in VL14 |
|-----------|-------------|
| **ModelLog + Y-snapshots** | Natuurlijk koppelvlak voor stopstate export/import; schema-contract bevriezen vóór implementatie |
| **Topology guard** | First-hit bisectie blijft default; brugvenster is enig toegestaan bypass-interval |
| **Contactvloer** | \(d\)-meting respecteert `max(3a, floor)`; documenteer of trigger op \(4a\) boven floor ligt |
| **Bundel / BEM** | Niet vereist voor ankerpaar; indien actief, state meenemen in export-hash |
| **Continuum (VL13)** | Optionele latere host; niet verplicht voor eerste GP-brug |
| **IPC/file-protocol** | Export bundle (Y-snapshot + meta JSON) → GP-worker → extractie-filament JSON → hervatting |

**Protocol-eisen (ontwerp):** deterministische bytes waar mogelijk; units SI in meta; expliciete velden `a_sim`, `xi_GP`, `bridgeVersion`, `gpEngine`, `inputHash`, `outputHash`, `topologyBefore`, `topologyAfter`, `extractStatus`.

---

## 6. Tests

| Fase | Test |
|------|------|
| Nu | Geen runtimewijziging |
| Na ACK | Contracttests op snapshot/bridge schema |
| Na ACK | Round-trip anker anti-parallel paar |
| Regressie | Geen-reconnectie-paden + topology guard default aan |
| Fail-pad | Gedwongen extractiefout → FAIL, geen tunnel |

---

## 7. Buiten scope

- Canonieke SST-klokwet / confirmatory VL07
- Continuum Taylor-kolom tenzij hergebruikt als host (VL13)
- Volledige quantumturbulentie / cascade-statistiek
- Stille uitschakeling topology guard in productiedefaults

---

## 8. ACK-checklist (Omar)

- [ ] Koplik–Levine-stop bij \(d\approx 4a\) + ModelLog-Y als koppelvlak is akkoord.
- [ ] Mislukte extractie moet hard FAIL zijn (geen tunneling).
- [ ] Provenance (GP-versie + hashes) verplicht bij hervatting.
- [ ] Topology guard blijft default aan buiten brugvenster.
- [ ] Round-tripcriteria op anti-parallel ankerpaar zijn scherp genoeg vóór code.
- [ ] **ACK:** implementatie mag starten · **NACK:** herzien ontwerp (geen code).

**ACK-ruimte:** datum / paraaf Omar: _______________
