# Uitgevoerde testvalidatie — 30 oktober 2026

- Broninventaris: A075 euler3d + ruban exact overeenkomstig de bronhashes in v0.2.9 en v0.2.10; A077 euler_field + pilotconfig overeenkomend met v0.1.2.
- Projectregressies: `pytest -q tests` **6/6 PASS**.
- End-to-end-generator: **A075 en A077** ieder uitgevoerd op n=16 en **48, 64, 80, 96** met passieve tracers en de originele Euler-rhs, periodiek gerasterde interpolatie, gedeelde RK4-stadia, output-ZIP en SHA-256.
- Twee langere korte termijnvoorbeelden op n=48, 20 stappen, absolute model-eindtijd t=0.02: **beide providers PASS** voor eindige, geëxporteerde vectortrajecten; geen fysieke gate.
- Duale orchestrator: zes uitvoerbare sequentiële onderruns (A075/A077, N=16/20/24) en samengesteld archief met hash **PASS**. De specifieke 48/64/80/96-campagne als één CLI-aanroep moet op Windows nog worden uitgevoerd; de acht individuele hogere-resolutie-runs zijn lokaal uitgevoerd.
- Boundary: periodieke unwrapped markeerposities. Tracerexport zegt niets over corecentroid, koppeling van materiële oppervlakken, Gaussische kernverhouding of spin.
- Niet getest: volledige ruimtelijke/tijd/finite-core/box-convergentie, native/GPU-backendpariteit voor dit nieuwe instrument, fysieke G8-gates, volledige lange run bij n=96 op Windows/Arc.

**Conclusie:** SOFTWARE_INTEGRATION_PASS / SCIENCE_UNRESOLVED. Dit is een gedeeld export-instrument, niet een geüpgradede A075 of A077 falsifierrelease.
