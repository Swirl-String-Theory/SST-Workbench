# Wetenschappelijk contract — A075 → A026

**Primair doel:** produceer originele, onafhankelijke, volledig 3D periodieke Euler-veldtrajecten, met materiaaltracerobservabelen die het bestaande `.npz`-invoercontract van A026-v0.1.0 respecteren.

**Niet getoetst:** aanwezigheid van een intrinsieke knoopklok, vertraagde achtergrondrespons van een parallel-kernenrooster, effectieve visco-elasticiteit, nieuwe fysica of topologische stabiliteit.

## Uitgesloten interpretaties

- Gaussian core smoothing != Ruban delta.
- Tagged passive fluid marker != knoopcentrum of getraceerde vorticiteitslijn.
- Numeriek reversibele energie != aangetoonde reversibele knoop/achtergrond-energietransfer.
- Onafhankelijke random seeds != onafhankelijke modelimplementaties of hardwarebackends.
- Een significant geschiedenisvoordeel na regressie != positieve fysische SST-kloktest.

## Exacte definities

De uit het Euler-veld geadvecteerde marker voldoet bij voldoende numerieke convergentie aan

\[ \dot{\mathbf X}(t)=\mathbf u(\mathbf X(t),t). \]

Met geselecteerde component `a` is

\[q(t)=L_* X_a(t),\qquad \dot q(t)=U_*u_a(\mathbf X(t),t),\qquad t_{\mathrm{SI}}=(L_*/U_*)t_{\mathrm{solver}}.\]

Daarmee zijn `[q]=m`, `[qdot]=m/s`, `[t]=s`. Circulatie en kinematische viscositeit schalen respectievelijk met `L_* U_*` en `L_* U_*`; hier blijft ν=0.

## Minimale kwalificatiecampagne (na deze patch)

1. Zelfde originele Ruban-seed en deterministische perturbatiereceptuur op minstens drie roosterresoluties, alle trajecten op vaste fysieke eindtijd; gebruik expliciete HSM-statistiek én grid-dependentie.
2. Temporele halvering met identieke beginvelden, eindtijd, interpolatie en seeds; niet opnieuw randomiseren per resolutie.
3. Core- en domeinladder; controleer dat knoopgrootte/box/core voldoende fysisch geresolveerd zijn.
4. Vastgelegde matched-state pairing en history-shuffle-negatieve controle, met groepen onafhankelijk toegewezen aan train/test.
5. Optioneel volledig teruggekoppelde parallelle vortexkernen als een **nieuwe** A075 initial-condition branch, met expliciete vorticiteitsdepositie en bronmanifesten.
6. Pas daarna onafhankelijke volledige achtergrondtoestands-orakeltest, energieflux-splitsing en klokfaseobservabele.

**Stopregel:** iets anders dan het volledige gateprogramma mag alleen als `DEVELOPMENT_ONLY`, `OBSERVATIONAL_DIAGNOSTIC` of `UNRESOLVED` worden gerapporteerd.
