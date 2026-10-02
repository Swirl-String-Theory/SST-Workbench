# Release notes — vortexring-lab v7.4.2

## Scope
- **Merge-build**: v7.4.1 auditcorrecties ⊕ SST-bundel r1 (research-track).

## Wijzigingen t.o.v7.4.1
- **Ω-scheiding**: HUD toont **Ω_core · Ω_bundle · Ω_wall** wanneer bundel actief is.
- **Vortexbundel UI**: `SST VORTEXBUNDEL · RESEARCH TRACK` paneel met profiel (parallel/splay/periodic), splaysterkte, bundelstraal, samplinglijnen, en optionele veldkoppeling.
- **Guards**
  - **Exclusiviteit**: bundelveldkoppeling en legacy `Ω_wall`-achtergrondkoppeling zijn wederzijds exclusief (UI + runtime).
  - **Wrijving blokkade**: bij actieve bundelveldkoppeling wordt wederzijdse wrijving uitgeschakeld (α=α′=0), omdat de combinatie zonder expliciete `v_n`-definitie in bundelveld ongedefinieerd is.
- **Selftests**: toegevoegd **T9a–T9e** (bundel/guards).

## Validatie
- Run `python validate-v7.4.2.py vortexring-lab-v7.4.2.html`
- Open `vortexring-lab-v7.4.2.html?selftest=1`
- Browser-smoke: minstens 10 frames zonder console errors / rode runtime-flag.

