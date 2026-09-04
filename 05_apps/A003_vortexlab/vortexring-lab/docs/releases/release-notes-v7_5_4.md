# Release notes — vortexring-lab v7.5.4

## Scope
- **Basis:** v7.5.3 stretch-gate + `vortexring-lab-v7_5_3_to_v7_5_4_stretch_gate-complete-fixes.diff`

## Wijzigingen t.o.v. v7.5.3
- **Passieve first-hit/trials:** transport-proxy en stretch-gate worden precies éénmaal over de geaccepteerde stap bijgewerkt; `advanceFilamentCandidate` centraliseert kandidaatintegratie.
- **Taylor-contact:** Taylor-forcing geldt uitsluitend in solo-modus en wordt vóór iedere contacttest in volle en gebisecteerde kandidaatstappen toegepast.
- **Exacte gap-ratio's:** `g_a = d_min/a_sim` plus aparte effectieve ratio voor de numerieke contactvloer.
- **Planck/String-schaalprobe:** passieve `a_probe`-metadata (metadata-only; stuurt nooit solver/BEM/contact).
- **String-probe medium + preset:** nieuw medium-segment en preset `String-theorie schaalprobe · ℓ_P`.
- **Regressiematrix:** zelftests uitgebreid met **T11–T13** (naast T0–T10g).
- **Provenance:** titel/footer/meta/selftest T0 gesynchroniseerd op `APP_VERSION`.

## Bestanden
- `vortexring-lab-v7_5_4.html` — canonieke build
- `validate-v7_5_4.py`
- `browser-smoke-v7_5_4.mjs`
- Rollback: `archive/v7/vortexring-lab-v7_5_3_stretch_gate.html`, `archive/v7/vortexring-lab-v7_5_2.html`, `archive/v7/vortexring-lab-v7_5_1.html`, `archive/v7/vortexring-lab-v7_5.html`

## Validatie
```bash
python validate-v7_5_4.py vortexring-lab-v7_5_4.html
node browser-smoke-v7_5_4.mjs vortexring-lab-v7_5_4.html
```
