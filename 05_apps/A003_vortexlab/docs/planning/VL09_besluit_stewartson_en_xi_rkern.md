# VL09 — Besluiten Stewartson + ξ↔r_kern

Datum: 2026-10-23 · Status: **vastgelegd, ACK-pending Omar**

## 1. Stewartson — Optie B

**Besluit:** Optie B — definitief geometrische visualisatie.

- Taylor-kolom, eindcaps en Stewartson-zijlaag blijven visualisatielagen.
- Dimensieloze q_S-proxy blijft beschikbaar.
- Geen kwantitatieve Ekman-sluiting E=ν/(ΩL²) in het inviscide filamentlab.
- Optie A (viscositeit/HVBK) vereist een apart gelabelde modeluitbreiding buiten deze epic-tranche.

Runtime-UI-tekst is bijgewerkt (info-paneel). Formele ACK van Omar nog open.

## 2. ξ↔r_kern conventiecheck

Sinds v7.5.1 is de open brug **ξ ↔ r_kern** (niet R_horn).

Track-B Δ in het GP-keuzepaneel blijft **conditioneel** tot deze checklist PASS is:

1. Documenteer ξ-definitie in Track-B kern-ODE (χ-fasepakket / Canon).
2. Documenteer a in U = Γ/(4πR)[ln(8R/a) − Δ].
3. Bewijs of weerleg identiteit van beide lengtes.
4. Pas daarna het UI-label «conditioneel» aan.

`coreFlowLock` default false is **DONE** (v7.5 / T0i) en hoort niet opnieuw besloten te worden.

## ACK

- [ ] Omar: Stewartson Optie B
- [ ] Omar / Canon: ξ↔r_kern check resultaat
