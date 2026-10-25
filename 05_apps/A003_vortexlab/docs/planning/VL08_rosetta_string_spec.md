# VL08 — Rosetta / String-afronding (ontwerp- en implementatiespec)

**Status:** spec geschreven · minimale runtime-hooks aanwezig · UI/kaarten/T14-volledig nog open  
**Parent-plan:** [`.cursor/plans/vortexlab_v7x/VL08_rosetta_string_afronding.plan.md`](../../../../.cursor/plans/vortexlab_v7x/VL08_rosetta_string_afronding.plan.md)  
**Bron:** Stappenplan v4/v5 §4 items 12–15; v6 §6; `VLResearchTrack.ROSETTA_DEFAULTS` in `research-track-vl.js`  
**Zelftest-id:** **T14** (niet T7 — T7 blijft ghost-invariantie)

---

## 1. Doel

Afronden van v7.6-S zonder Rosetta/String te koppelen aan de SST-klokwet of de filament-ODE, behalve via de expliciete expertmodus `radiusDrive='simulation'`.

Aanwezig vóór VL08: `PLANCK_LENGTH`, He-core-ref, passieve `a_probe` / Planck-presets, R_horn / r_kern / a_sim-scheiding, log-slider op `a_probe` (orde \(10^{-36}\)–\(10^{-9}\) m).

---

## 2. classicalE2-alias

| Item | Spec |
|------|------|
| Naam | `classicalE2` |
| Resolutie | **Alias van `sstCore`** (niet een tweede ijkpunt) |
| Fysische lezing | \(\tfrac12 r_e \approx r_c\) is een **SST-identificatie**, geen onafhankelijke externe kalibratie |
| Runtime | `VLResearchTrack.ROSETTA_DEFAULTS.classicalE2AliasOf === 'sstCore'`; helper `classicalE2ResolvesTo()` |
| Verboden | Aparte medium-/kernmodellenstroom of tweede Canon-constantenpad onder de naam classicalE2 |

---

## 3. Log-slider (`a_probe`)

| Item | Spec |
|------|------|
| Besturing | Bestaande `#sScaleProbeLog` (log₁₀ van meters) + tekstveld + presets |
| Bereik-doel | ~**29 ordes** (Planck ↔ lab/He-schalen); huidig HTML-bereik min/max mag bij UI-tranche worden bijgesteld |
| Semantiek | Alleen `P.scaleProbe`; **nooit** stilzwijgend `P.a` / r_kern / R_horn / BEM / contact |
| ModelLog | `scaleProbe` met `passive:true` zolang `radiusDrive !== 'simulation'` |

---

## 4. `runTheory`

| Waarde | UI/medium-mapping | Gedrag |
|--------|-------------------|--------|
| `He-II` | `med='he'` | κ-quanta; He-core-ref als probe-default |
| `SST` | `med='sst'` (default) | Γ₀ / R_horn / Research-Track |
| `String/Rosetta` | `med='string'` | Vrije Γ; Planck-probe metadata; **geen** snaardynamica |

- Veld: `P.runTheory`, gesynchroniseerd vanuit medium (`syncRunTheoryFromMed`).
- Default uit `ROSETTA_DEFAULTS.runTheory` (`'SST'`).
- Tension-proxy: **alleen readout**; geen energieclaim.
- α_ring-naamgevingsfirewall: UI/docs mogen α_ring^GP niet stilzwijgend als α_fs of φ presenteren (bestaande χ-caveats blijven).

---

## 5. Rosetta-kaarten (readouts)

Vier kaarten (UI later; runtime-helper `rosettaReadoutCards()`):

| Kaart | Definitie | Eenheid |
|-------|-----------|---------|
| \(a/\ell_P\) | `scaleProbe / PLANCK_LENGTH` | dimensieloos |
| \(a/r_c\) | `scaleProbe / R_HORN_SST` (horn als canonieke SST-referentieschaal in Rosetta-audit; **niet** claim \(a=r_c=r_{\rm kern}\)) | dimensieloos |
| \(R/a\) | karakteristieke filamentstraal (ring \(R_0\) of actuele mean \(R\)) / `scaleProbe` | dimensieloos |
| \(\log_{10} a\) | `log10(scaleProbe)` | log₁₀(m) |

Kaarten zijn diagnostiek; ze sturen de solver niet.

---

## 6. `radiusDrive`

| Modus | Default? | Effect |
|-------|----------|--------|
| `'physical-only'` | **ja** | `a_probe` blijft metadata; `applyScaleProbeToSimRadius` is no-op; Planck-preset wijzigt filamentdynamica niet |
| `'simulation'` | nee (expert) | Mag `a_probe` → `a_sim` koppelen na expliciete bevestiging + waarschuwing; numerieke Biot–Savart-vloer blijft (`A_SIM_INPUT_FLOOR` e.d.) |

**Acceptatiegate:** verse start `radiusDrive='physical-only'`; Planck-preset verandert `velocityCore`-hash niet zolang modus ≠ `'simulation'`.

Bewuste planafwijking sinds v7.3 (\(a<1\,\mu\mathrm{m}\) open) wordt door deze guardrail **gesloten** voor de defaultpad.

---

## 7. Zelftest T14 (niet T7)

| Id | Onderwerp |
|----|-----------|
| **T7** | Ghost Stewartson dynamisch krachteloos (bit-identiek) — **ongewijzigd** |
| **T14** | Planck-preset / `a_probe`-wissel: filamentdynamica bit-identiek zolang `radiusDrive !== 'simulation'`; default `physical-only`; `classicalE2` alias = `sstCore`; `planckInvariantSelftestId === 'T14'` |

T14 bouwt voort op T11 (passieve probe) maar bindt expliciet aan `radiusDrive` en de VL08-defaults.

---

## 8. Koppelvlak runtime

| Component | Rol |
|-----------|-----|
| `research-track-vl.js` → `ROSETTA_DEFAULTS` | Canonieke defaults + T14-id |
| `vortexlab-runtime.js` | `P.radiusDrive`, `P.runTheory`, helpers, ModelLog-velden, T14 |
| `index.html` | Latere UI: runTheory-seg, Rosetta-kaarten, radiusDrive-toggle + confirm |
| SelfTest PKEYS | Snapshot/restore voor `radiusDrive`, `runTheory` |

---

## 9. Gates / acceptatie

1. Default start: `radiusDrive='physical-only'`, `runTheory='SST'`.
2. Simulation-modus logt waarschuwing + vereist expliciete bevestiging (UI-tranche).
3. Geen energieclaim op tension-proxy.
4. `npm run check` / `verify-parity` groen na hash-update bij runtimewijziging.
5. Browser `?selftest=1`: T14 groen naast T7/T11–T13.

---

## 10. Versie / buiten scope

- Patch op 7.6.x-lijn of label `7.6.S1` bij volledige UI-afronding — kiezen bij die tranche.
- Geen solverkoppeling van Rosetta naar klokwet.
- ξ↔r_kern documentgate = **VL09** (niet hier).
- Continuum / Ekman = VL13.
