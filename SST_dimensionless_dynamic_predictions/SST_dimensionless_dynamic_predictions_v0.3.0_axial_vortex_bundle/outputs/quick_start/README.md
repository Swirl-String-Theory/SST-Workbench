# Quick-start campaign — resultaat

**Status:** smoke test; geen prediction claim.

Protocol: fixed length `L=2π`, `Γ=1`, resolution 64, `ε=0.08`, 40 RK4 steps, Rosenhead en Winckelmans kernels.

| Kernel | State | Relative residual | Energy ratio | Rigid-rate ratio | Final recurrence error | Energy drift |
|---|---:|---:|---:|---:|---:|---:|
| rosenhead | ring | 4.26115e-15 | 1 | 1 | 6.45719e-16 | -5.08867e-16 |
| rosenhead | trefoil | 0.214591 | 0.763269 | 2.36888 | 0.00863415 | -0.00147478 |
| rosenhead | mirror_trefoil | 0.214591 | 0.763269 | 2.36888 | 0.00802596 | -0.00135352 |
| rosenhead | figure_eight | 0.429659 | 0.558669 | 2.78722 | 0.031396 | -0.010114 |
| winckelmans | ring | 5.68047e-15 | 1 | 1 | 6.47109e-16 | -5.08867e-16 |
| winckelmans | trefoil | 0.215653 | 0.763269 | 2.32465 | 0.00856018 | -0.00151197 |
| winckelmans | mirror_trefoil | 0.215653 | 0.763269 | 2.32465 | 0.00798292 | -0.00138862 |
| winckelmans | figure_eight | 0.442747 | 0.558669 | 2.83676 | 0.0337979 | -0.0106847 |

## Eerste lezing

- De ring passeert de relative-equilibrium-gate tot numerieke precisie.
- De statische trefoil en mirror-trefoil geven dezelfde parity-even energie en vrijwel dezelfde dynamische diagnostiek, zoals verwacht.
- De trefoil-residual blijft rond 0.215 en faalt de 5%-gate.
- De figure-eight-residual ligt rond 0.43–0.44 en faalt sterker.
- De korte evolutie behoudt de ringvorm; de knopen ontwikkelen meetbare recurrence error.
- De energy proxy-ratio is in dit prototype circa 0.763 voor de trefoil en 0.559 voor de figure-eight onder fixed-length normalisatie. Dit zijn modeloutputs, geen universele waarden.
- De quick run is te kort voor een betrouwbare dominante frequentie; het script rapporteert daarom geen frequentieratio.

## Falsificatiebetekenis

Deze smoke test reproduceert de kwalitatieve hoofdbevinding van de eerdere audit: een ideal-knot centerline is niet automatisch een relative equilibrium van de gekozen regularized Biot–Savart operator.

## Volgende computationele stap

Voer eerst een constrained relative-state solve uit voor `3_1`, gevolgd door een resolutie- en kernel-ladder. Pas een geconvergeerde kleine-residual toestand mag worden gebruikt voor een echte frequency/action-ratio.