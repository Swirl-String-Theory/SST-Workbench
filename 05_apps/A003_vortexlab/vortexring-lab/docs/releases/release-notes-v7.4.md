# vortexring-lab v7.4 (a) — release notes

**Basis:** jouw v7.3.1-hotfix (canoniek genomen; jullie validator draait PASS op deze build, in een naar 7.4 aangepaste variant meegeleverd als `validate-v7.4.py`). Erkenning vooraf: de ACN temporal-dead-zone die v7.3.1 repareerde was mijn fout in de v7.3-diaghook — de log-aanroep stond vóór de `const ACN`-declaratie. Terecht gevangen; jullie "niet accepteren"-lijst (node --check is geen runtimebewijs) is een structurele les die blijft staan.

## Scope

Dit is de **kleine, risicoloze helft** van plan-Fase 3 ("wetenschappelijke positionering"), conform de aanbevolen volgorde. Bewust **niet** in deze patch: de frame-ontvlechting (punt 6 — eigen refactorpatch, v7.4b), het Stewartson-eindbesluit (punt 4 — jouw beslissing: Ekman-sluiting of definitief visueel), ε_rev-uitlezing (hoort bij de frame/omkeer-machinerie) en de `coreFlowLock`-defaultwissel (beslispunt: breekt SST-preset-ergonomie).

## Wijzigingen

1. **Ê_eff → geometrische score Ŝ.** Kaartlabel hernoemd ("geo-score Ŝ · geen energie") en de docs documenteren nu expliciet de γĤ-tekengevoeligheid: spiegelknopen (Ĥ→−Ĥ) krijgen een verschillende score zonder pariteitsbrekend mechanisme in het model; wie chiraliteits-neutraal wil rangschikken gebruikt γ|Ĥ|. De getekende vorm blijft beschikbaar als gedocumenteerde keuze.
2. **Rankine display-similarity-label** op de kernkoppelings-checkbox. De default (`coreFlowLock:true`) is ongewijzigd — dat is het genoemde beslispunt, geen omissie.
3. **Dimensieloze HUD-rij χ_Ω · Ro · a/R.** χ_Ω = Γ/(2πa²Ω) via het al bestaande `coreFlowRatio()` (conform verificatie-item 16: exposen, niet herbouwen); Ro = |v_z,rel|/(2|Ω|R_cyl), '—' bij Ω≈0; ε = a/R_ring. Adaptief geformatteerd (exponentieel buiten [10⁻³,10⁴]). g_a = d_min/a is doorgeschoven: die vereist de O(N²)-gap per HUD-tick of hergebruik van het 12-frame-stabiliteitsrapport — komt met v7.4b.
4. **GP-ringconstante als provenance-keuze** (nieuw paneel, audit-item 15 afgehandeld zoals gepland): default Roberts–Grant 1971 · 0.615 (literatuur); optioneel SST Track B v12B.0 · 0.6193509, expliciet gelabeld *in-house, conditioneel op de openstaande a↔ξ-radiusconventiecheck*. Wissel muteert `DELTA.gp`, logt naar ModelLog en triggert reset (Δ zit in de LIA-prefactor).
5. **Γ_A·Γ_B-tekenuitlezing** in botsing-modus (+1 gelijk-roterend / −1 tegengesteld, uit ccwA/ccwB) — sluit audit-restpunt 17.
6. **"tijd terug" → "achterwaarts integreren"** (label; de α≠0-antidissipatie-waarschuwing bestond al).

## Provenance

`APP_VERSION='7.4'`, `APP_BASE_VERSION='7.3.1'`, meta bijgewerkt, en de hardcoded basecheck in zelftest-T0 mee-geüpdatet zodat T0 consistent blijft.

## Validatie

Statische validator (7.4-variant van jullie script): PASS, inclusief node --check en dubbele-ID-check. Fysica-regressie (node): B1-modusscheiding, B3-ghost-ontkoppeling, wrijvingsidentiteiten — alle groen; geen van de zes wijzigingen raakt integrator, contactdetectie of topologie-kernen. **Conform jullie eigen eis blijft de browsertest verplicht:** ≥10 frames zonder console-errors, `?selftest=1` (T0–T6), en visuele check dat de nieuwe HUD-rij en het GP-paneel verschijnen — dat kan ik vanuit deze omgeving niet afdwingen.

## Openstaand voor v7.4b

Frame-ontvlechting solver/display/backgroundFlow + E_frame < 10⁻⁶-test, ε_rev-HUD, g_a-uitlezing, en de twee beslispunten (Stewartson, coreFlowLock-default). Daarna v7.6-S (String/Rosetta-afronding met radiusDrive-guardrails + zelftest-T7).
